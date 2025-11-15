from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        try:
            # Navigate to the application
            page.goto("http://localhost:5173")

            # Click on the 'Color Picker' artifact card
            color_picker_card = page.get_by_text("Color Picker")
            expect(color_picker_card).to_be_visible(timeout=10000)
            color_picker_card.click()

            # Wait for the modal to appear and the artifact to load
            expect(page.get_by_text("Validating artifact...")).to_be_visible()
            # Wait for validation to complete and the component to be visible
            # The color picker component has a specific button text
            expect(page.get_by_role("button", name="Pick Color")).to_be_visible(timeout=10000)

            # Take a screenshot of the loaded artifact
            page.screenshot(path="jules-scratch/verification/verification.png")

            print("Screenshot saved to jules-scratch/verification/verification.png")

        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="jules-scratch/verification/error.png")

        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()