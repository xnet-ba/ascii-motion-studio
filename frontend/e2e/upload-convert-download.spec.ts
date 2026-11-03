import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'
import os from 'os'

const TOKEN = process.env.AMS_TEST_TOKEN || ''
const BASE_URL = process.env.BASE_URL || 'https://go.kolektiv.pro'

async function createTestImage(): Promise<string> {
  const dir = await fs.promises.mkdtemp(path.join(os.tmpdir(), 'ams-e2e-'))
  const filePath = path.join(dir, 'test.png')
  // 2x2 green PNG
  const base64 = 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAE0lEQVQIW2Nk+M8wABMhEwwDQQA3CQj//ij8pgAAAABJRU5ErkJggg=='
  await fs.promises.writeFile(filePath, Buffer.from(base64, 'base64'))
  return filePath
}

test('upload, convert and download ASCII image', async ({ page }) => {
  test.setTimeout(120000)
  test.skip(!TOKEN, 'AMS_TEST_TOKEN not set')
  const imagePath = await createTestImage()

  // Upload and convert via API; the UI is exercised for review/download.
  const uploadResp = await page.request.post(`${BASE_URL}/api/v1/upload`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
    multipart: {
      file: {
        name: 'test.png',
        mimeType: 'image/png',
        buffer: await fs.promises.readFile(imagePath),
      },
    },
  })
  expect(uploadResp.ok()).toBeTruthy()
  const uploaded = await uploadResp.json()

  const convertResp = await page.request.post(`${BASE_URL}/api/v1/image/convert`, {
    headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    data: {
      input_path: uploaded.path,
      width: 10,
      mode: 'grayscale',
      background: 'black',
      output_format: 'html',
    },
  })
  expect(convertResp.ok()).toBeTruthy()
  const { job_id } = await convertResp.json()

  await page.goto('/')
  await page.evaluate((t) => localStorage.setItem('ams_token', t), TOKEN)
  await page.goto('/')

  await page.getByRole('button', { name: /poslovi/i }).first().click()
  await expect(page.locator(`text=#${job_id}`)).toBeVisible({ timeout: 60000 })
  await expect(page.locator('text=completed').first()).toBeVisible({ timeout: 60000 })
  await expect(page.locator('text=Preuzmi').first()).toBeVisible()

  await fs.promises.rm(path.dirname(imagePath), { recursive: true, force: true })
})
