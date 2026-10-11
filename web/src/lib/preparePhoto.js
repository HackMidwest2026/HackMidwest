// Get a resident's photo ready to upload, whatever format their device produced.
//
// The browser decodes the file (JPEG, PNG, WebP, GIF, AVIF, BMP, and HEIC on Safari), then it
// is redrawn upright at up to MAX_SIDE px and re-encoded as JPEG. That keeps uploads small
// (phone photos are 3-15 MB) and drops metadata such as GPS before the file leaves the device.
// iPhone HEIC/HEIF photos that the browser can't decode go through heic2any, loaded only
// when needed. If nothing here can read the file (for example TIFF outside Safari), the
// original is sent and the server converts it.
const MAX_SIDE = 2048
const QUALITY = 0.85
export const MAX_PHOTO_BYTES = 40 * 1024 * 1024

const isHeic = (file) => /image\/hei[cf]/i.test(file.type) || /\.hei[cf]$/i.test(file.name || '')

async function decode(blob) {
  // imageOrientation: 'from-image' applies the camera's rotation flag.
  return createImageBitmap(blob, { imageOrientation: 'from-image' })
}

async function heicToJpeg(file) {
  const { default: heic2any } = await import('heic2any')
  const out = await heic2any({ blob: file, toType: 'image/jpeg', quality: 0.92 })
  return Array.isArray(out) ? out[0] : out // multi-image HEIC: use the first
}

function toJpeg(bitmap) {
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
  const w = Math.max(1, Math.round(bitmap.width * scale))
  const h = Math.max(1, Math.round(bitmap.height * scale))
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#fff' // transparent areas become white, not black
  ctx.fillRect(0, 0, w, h)
  ctx.drawImage(bitmap, 0, 0, w, h)
  bitmap.close?.()
  return new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('encode failed'))), 'image/jpeg', QUALITY))
}

const jpegName = (name) => `${(name || 'photo').replace(/\.[^.]+$/, '')}.jpg`

/**
 * Returns { file, converted, from } where file is the Blob to upload and preview.
 * Throws an Error with a message for the resident if the file can't be used.
 */
export async function preparePhoto(file) {
  if (!file) return null
  if (file.size > MAX_PHOTO_BYTES) throw new Error('That photo is over 40 MB. Choose a smaller one.')
  if (file.type && !file.type.startsWith('image/') && !isHeic(file)) throw new Error('That file is not an image. Choose a photo.')
  if (/svg/i.test(file.type)) throw new Error('SVG files are not accepted. Choose a photo.')
  const from = isHeic(file) ? 'HEIC' : (file.type.split('/')[1] || file.name.split('.').pop() || 'image').toUpperCase()

  let bitmap = null
  try {
    bitmap = await decode(file)
  } catch {
    if (isHeic(file)) {
      try {
        bitmap = await decode(await heicToJpeg(file))
      } catch {
        throw new Error('This HEIC photo could not be converted. Export it as JPEG and try again.')
      }
    }
  }
  if (!bitmap) return { file, converted: false, from } // the server will convert it if it can

  const blob = await toJpeg(bitmap)
  return { file: new File([blob], jpegName(file.name), { type: 'image/jpeg' }), converted: true, from }
}
