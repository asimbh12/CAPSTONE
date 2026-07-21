import { expect, test } from '@playwright/test'

test('creates, searches, evidences, and archives a career asset', async ({ page }) => {
  const title = `Stage 3 leadership asset ${Date.now()}`
  await page.goto('/')
  await expect(page.getByText('Local API online')).toBeVisible()

  await page.getByRole('button', { name: 'Career assets' }).click()
  await page.getByRole('button', { name: 'Add career asset' }).click()
  await page.getByLabel('Asset title').fill(title)
  await page.getByLabel('Description').fill('A public professional leadership contribution.')
  await page.getByLabel('Impact summary').fill('Convened a professional community around a shared objective.')
  await page.getByLabel('Start date').fill('2026-01-15')
  await page.getByRole('button', { name: 'Save asset' }).click()

  await expect(page.getByText('Career asset created.')).toBeVisible()
  await page.getByLabel('Search assets').fill(title)
  await expect(page.getByRole('heading', { name: title })).toBeVisible()
  await page.getByRole('heading', { name: title }).click()

  await page.getByLabel('Evidence title').fill('Official public record')
  await page.getByLabel('Public source URL').fill('https://example.org/public-record')
  await page.getByLabel('What this evidence demonstrates').fill('Confirms the public professional contribution.')
  await page.getByRole('button', { name: 'Add evidence' }).click()
  await expect(page.getByText('Official public record')).toBeVisible()

  await page.getByRole('button', { name: 'Archive' }).click()
  await expect(page.getByRole('heading', { name: title })).not.toBeVisible()
})
