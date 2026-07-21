import { expect, test } from '@playwright/test'

test('loads the CAPSTONE foundation with a healthy API', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: /turn career experience/i })).toBeVisible()
  await expect(page.getByText('API online · v0.1.0')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Career assets', exact: true })).toBeVisible()
})
