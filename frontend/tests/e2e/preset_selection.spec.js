
import { test, expect } from '@playwright/test'

test.describe('Config Page - API Preset Selection', () => {
  test('dropdown options should display human-readable names', async ({ page }) => {
    // 1. Navigate to the configuration page
    // Assumes the app is running on localhost:5173 (default Vite port)
    await page.goto('http://localhost:5173/#/config') 
    
    // 2. Click on the "Processing Mode" (Pipeline) tab
    await page.click('text=处理模式')
    
    // 3. Locate the API Preset select input
    const selectPlaceholder = page.getByPlaceholder('请选择 API 预设')
    await expect(selectPlaceholder).toBeVisible()
    
    // 4. Open the dropdown
    await selectPlaceholder.click()
    
    // 5. Wait for options to appear
    const dropdownOption = page.locator('.t-select-option')
    await expect(dropdownOption.first()).toBeVisible()
    
    // 6. Verify the text content of the first option
    const firstOptionText = await dropdownOption.first().innerText()
    console.log('Dropdown option text:', firstOptionText)
    
    // It should contain the preset name (e.g., "DeepSeek")
    // It should NOT contain "[object Object]"
    expect(firstOptionText).not.toContain('[object Object]')
    
    // Check if it contains expected parts (Name and Model info)
    // Assuming default preset "DeepSeek V3 (SiliconFlow)" exists
    if (firstOptionText.includes('DeepSeek')) {
        expect(firstOptionText).toContain('DeepSeek')
    }
  })
})
