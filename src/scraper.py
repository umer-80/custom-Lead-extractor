from playwright.async_api import async_playwright

class SentinelScraper:
    def __init__(self):
        pass    

    async def search_google_maps(self, niche: str, location: str):
        """
        Searches Google Maps for the given niche and location.
        Returns a list of leads with detailed info (Phone, Website, Address).
        """
        leads = []
        async with async_playwright() as p:
            # Launch browser (headless=True for speed, False for debug)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 1. Search
            query = f"{niche} in {location}"
            try:
                await page.goto(f"https://www.google.com/maps/search/{query}")
                await page.wait_for_selector('div[role="feed"]', timeout=10000)
            except Exception as e:
                print(f"Error scraping Google Maps: {e}")
                await page.screenshot(path="debug_error.png") # Capture error state
                await browser.close()
                return []

            # Initial wait for results
            try:
                # Wait for at least one result to appear
                await page.wait_for_selector('div[role="article"]', timeout=5000)
            except:
                 print("No results found immediately. Taking screenshot...")
                 await page.screenshot(path="debug_no_results.png")
                 await browser.close()
                 return []

            # 2. Scroll to load more results
            feed_selector = 'div[role="feed"]'
            for _ in range(5):  # Scroll a few times
                await page.locator(feed_selector).evaluate("el => el.scrollTop = el.scrollHeight")
                await page.wait_for_timeout(2000)

            # 3. Click & Extract (The "Real Work")
            # We get all items first
            items = await page.locator('div[role="article"]').all()
            
            # Limit to 5 for now to test the "Quality" over "Quantity" (Can increase later)
            for i, item in enumerate(items[:5]):
                try:
                    # Click the item to open details
                    await item.click()
                    
                    # Wait for details panel. 
                    # The Details panel usually has role="main" AND an aria-label (the business name).
                    # The List panel often does not have an aria-label or is different.
                    # We can target the *second* main or specifically one with aria-label.
                    try:
                        await page.wait_for_selector('div[role="main"][aria-label]:not([aria-label=""])', timeout=5000)
                    except:
                        # Sometimes it might be just role="main" if only one exists (unlikely given error)
                        # Let's try grabbing the last one
                        pass
                        
                    await page.wait_for_timeout(2000) # Stability pause
                    
                    # Extract Data from Details Panel
                    # Use .last to ensure we get the details panel if multiple exist
                    main_div = page.locator('div[role="main"][aria-label]').last
                    
                    # Extract Place ID from the link in the article
                    # Note: item is the div[role="article"] from the list
                    place_id = "Unknown"
                    try:
                        link_element = item.locator('a').first
                        href = await link_element.get_attribute("href")
                        if href:
                            # Place ID is often after /place/ and before /data/
                            # or in the 1s... parameter
                            import re
                            # Try to find ChIJ pattern (27 chars starting with ChIJ)
                            place_id_match = re.search(r'ChIJ[a-zA-Z0-9_-]{23}', href)
                            if place_id_match:
                                place_id = place_id_match.group(0)
                            else:
                                # Fallback: extract from Feature ID if possible
                                # This is a bit more complex, let's stick to ChIJ for now
                                pass
                    except:
                        pass

                    # Name is h1 inside the main div
                    name = await main_div.locator('h1').first.inner_text()
                    
                    # Filter out Ads/Sponsored
                    if "Sponsored" in name or "Ad" in name:
                         continue
                    
                    # ... (rest of extraction) ...
                    
                    # Rating & Reviews
                    text_content = await main_div.inner_text()
                    
                    import re
                    rating_match = re.search(r"(\d\.\d)\s*\((\d+[,\d]*)\)", text_content)
                    rating = float(rating_match.group(1)) if rating_match else 0.0
                    reviews = 0
                    if rating_match:
                         reviews = int(rating_match.group(2).replace(",", ""))
                         
                    # Website
                    # Look for button that says "Website"
                    website = "None"
                    try:
                        website_btn = page.locator('a[data-item-id="authority"]')
                        if await website_btn.count() > 0:
                            website = await website_btn.get_attribute("href")
                        else:
                            # Fallback: look for aria-label="Website: ..."
                            potential_btns = page.locator('a[aria-label*="Website"]')
                            if await potential_btns.count() > 0:
                                website = await potential_btns.first.get_attribute("href")
                    except:
                        pass
                        
                    # Phone
                    # Look for button with phone icon data (starts with "tel:") but usually just text
                    # We regex the text content for phone pattern or look for specific button
                    phone = "None"
                    try:
                        # Common pattern: button with data-item-id starts with "phone"
                        phone_btn = page.locator('button[data-item-id*="phone"]')
                        if await phone_btn.count() > 0:
                            phone = await phone_btn.get_attribute("aria-label")
                            if phone:
                                phone = phone.replace("Phone: ", "")
                        else:
                             # Regex fallback
                             phone_match = re.search(r"\(\d{3}\)\s\d{3}-\d{4}", text_content)
                             if phone_match:
                                 phone = phone_match.group(0)
                    except:
                        pass

                    lead = {
                        "name": name,
                        "place_id": place_id,
                        "rating": rating,
                        "reviews": reviews,
                        "website": website,
                        "phone": phone
                    }
                    leads.append(lead)

                    
                    # Go back to list if needed, or just clicking next item works?
                    # Clicking next item works if 'items' references are still valid.
                    # Usually clicking another item on the left works. 
                    
                except Exception as e:
                    print(f"Error scraping lead {i}: {e}")
                    continue
            
            await browser.close()
            return leads

    async def visit_website(self, url: str):
        """
        Visits a website to perform a Multi-Stage Audit (v4.0).
        """
        import re
        tech_stack = {
            "has_chatbot": False,
            "has_booking": False,
            "social_links": [],
            "email": "None",
            "is_ssl": url.startswith("https"),
            "is_mobile_ready": False,
            "site_status": "Down",
            "copyright_year": "Unknown",
            "detected_phones": []
        }
        
        if url == "None" or not url:
            tech_stack["site_status"] = "No Website"
            return tech_stack

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                # Set timeout to 15s
                try:
                    response = await page.goto(url, timeout=15000, wait_until="domcontentloaded") 
                except:
                    tech_stack["site_status"] = "Timeout/Error"
                    return tech_stack
                
                if response and response.status < 400:
                    tech_stack["site_status"] = "Up"
                else:
                    tech_stack["site_status"] = f"Error {response.status if response else 'Unknown'}"

                # 1. Mobile Check (Viewport Meta)
                viewport_meta = await page.locator('meta[name="viewport"]').count()
                tech_stack["is_mobile_ready"] = viewport_meta > 0

                content = await page.content()
                content_lower = content.lower()
                
                # 2. Age Detection (Copyright)
                # Look for "Copyright © 202X" or "© 202X"
                copyright_match = re.search(r'(?:copyright|©)\s*(?:20)?(\d{2,4})', content_lower)
                if copyright_match:
                    tech_stack["copyright_year"] = copyright_match.group(1)

                # 3. Contact Intelligence (Phone & Socials)
                # Phone Regex (targeting AU numbers and general patterns)
                # Mobile patterns: 04XX XXX XXX
                phone_pattern = r'(?:\+?61|0)4(?:[ -]?[0-9]){8}|(?:\+?61|0)[2-9](?:[ -]?[0-9]){8}'
                found_phones = re.findall(phone_pattern, content)
                tech_stack["detected_phones"] = list(set(found_phones))

                # Chatbot & Booking
                chatbot_keywords = ['chat with us', 'live chat', 'intercom', 'drift', 'zendesk', 'crisp', 'tawk.to', 'chatbot']
                if any(keyword in content_lower for keyword in chatbot_keywords):
                    tech_stack["has_chatbot"] = True
                
                booking_keywords = ['book now', 'schedule appointment', 'book online', 'calendly', 'acuity', 'setmore', 'booking']
                if any(keyword in content_lower for keyword in booking_keywords):
                    tech_stack["has_booking"] = True
                
                # Social Links
                social_domains = ['facebook.com', 'instagram.com', 'linkedin.com', 'twitter.com', 'x.com', 'tiktok.com', 'youtube.com']
                links = await page.locator("a").all()
                for link in links:
                    try:
                        href = await link.get_attribute("href")
                        if href:
                            # Socials
                            for domain in social_domains:
                                if domain in href and href not in tech_stack["social_links"]:
                                    tech_stack["social_links"].append(href)
                            
                            # Email (mailto:)
                            if "mailto:" in href and tech_stack["email"] == "None":
                                 tech_stack["email"] = href.replace("mailto:", "").split("?")[0].strip()
                    except:
                        continue

                # Regex Fallback for Email
                if tech_stack["email"] == "None":
                     email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", content)
                     if email_match:
                         candidate = email_match.group(0)
                         if not any(x in candidate.lower() for x in ['.png', '.jpg', '.jpeg', 'sentry', 'react', 'wix', 'wordpress']):
                             tech_stack["email"] = candidate

            except Exception as e:
                # print(f"Audit Error: {e}")
                pass
            finally:
                await browser.close()
                
        return tech_stack

