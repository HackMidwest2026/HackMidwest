// Report photos in different formats are stored as upright, resized JPEGs without metadata.
import assert from 'node:assert/strict'
import { describe, test } from 'node:test'
import sharp from 'sharp'

const { normalizePhoto, parseDataUrl, PhotoError } = await import('../src/lib/images.js')

const solid = (w, h, extra = {}) => sharp({ create: { width: w, height: h, channels: extra.alpha ? 4 : 3, background: extra.alpha ? { r: 200, g: 30, b: 30, alpha: 0 } : '#c81e1e' } })
const dataUrl = (mime, buf) => `data:${mime};base64,${buf.toString('base64')}`

describe('photo formats', () => {
  for (const [name, mime, make] of [
    ['JPEG', 'image/jpeg', () => solid(64, 48).jpeg().toBuffer()],
    ['PNG', 'image/png', () => solid(64, 48).png().toBuffer()],
    ['WebP', 'image/webp', () => solid(64, 48).webp().toBuffer()],
    ['GIF', 'image/gif', () => solid(64, 48).gif().toBuffer()],
    ['AVIF', 'image/avif', () => solid(64, 48).avif().toBuffer()],
    ['TIFF', 'image/tiff', () => solid(64, 48).tiff().toBuffer()],
  ]) {
    test(`${name} is stored as JPEG`, async () => {
      const { declared, bytes } = parseDataUrl(dataUrl(mime, await make()))
      const out = await normalizePhoto(bytes, declared)
      assert.equal(out.mime, 'image/jpeg')
      assert.equal(out.ext, 'jpg')
      const meta = await sharp(out.bytes).metadata()
      assert.equal(meta.format, 'jpeg')
      assert.deepEqual([meta.width, meta.height], [64, 48])
    })
  }

  test('a wrong or missing declared type does not matter: the bytes decide', async () => {
    const png = await solid(10, 10).png().toBuffer()
    for (const url of [dataUrl('image/jpeg', png), `data:application/octet-stream;base64,${png.toString('base64')}`, `data:;base64,${png.toString('base64')}`]) {
      const { declared, bytes } = parseDataUrl(url)
      assert.equal((await normalizePhoto(bytes, declared)).mime, 'image/jpeg')
    }
  })

  test('phone photos are turned upright, scaled down and stripped of GPS metadata', async () => {
    // 4000x3000 sensor image tagged "rotate 90°" (orientation 6), with GPS coordinates.
    const raw = await solid(4000, 3000)
      .jpeg()
      .withMetadata({ orientation: 6, exif: { IFD0: { Make: 'TestPhone' }, IFD3: { GPSLatitudeRef: 'N', GPSLatitude: '39/1 3/1 0/1', GPSLongitudeRef: 'W', GPSLongitude: '94/1 34/1 0/1' } } })
      .toBuffer()
    const before = await sharp(raw).metadata()
    assert.ok(before.exif && before.orientation === 6 && raw.includes(Buffer.from('TestPhone')), 'fixture has EXIF')
    const out = await normalizePhoto(raw, 'image/jpeg')
    const meta = await sharp(out.bytes).metadata()
    assert.deepEqual([meta.width, meta.height], [1536, 2048]) // portrait, longest side 2048
    assert.equal(meta.exif, undefined)
    assert.equal(meta.orientation, undefined)
    assert.ok(!out.bytes.includes(Buffer.from('TestPhone')))
  })

  test('transparent areas become white, not black', async () => {
    const out = await normalizePhoto(await solid(8, 8, { alpha: true }).png().toBuffer(), 'image/png')
    const { data } = await sharp(out.bytes).raw().toBuffer({ resolveWithObject: true })
    assert.ok(data[0] > 240 && data[1] > 240 && data[2] > 240)
  })

  test('non-images, SVG and broken data are refused with a clear message', async () => {
    const svg = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><script>alert(1)</script></svg>')
    await assert.rejects(normalizePhoto(svg, 'image/svg+xml'), (e) => e instanceof PhotoError && e.status === 400 && /SVG/.test(e.message))
    await assert.rejects(normalizePhoto(Buffer.from('%PDF-1.7 not an image'), 'application/pdf'), (e) => e instanceof PhotoError && /isn't an image/.test(e.message))
    // HEIC that the server can't decode gets a specific hint (the website converts it first).
    const heicHeader = Buffer.concat([Buffer.from([0, 0, 0, 24]), Buffer.from('ftypheic'), Buffer.alloc(40)])
    await assert.rejects(normalizePhoto(heicHeader, 'image/heic'), (e) => e instanceof PhotoError && /HEIC/.test(e.message))
    assert.throws(() => parseDataUrl('not a data url'), PhotoError)
    assert.throws(() => parseDataUrl('data:image/png;base64,'), PhotoError)
  })
})
