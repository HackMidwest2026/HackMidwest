// Report photos arrive in whatever format the resident's phone or camera produced. Every photo
// is normalized to a JPEG here, so storage, the browser and the Vision agent (Bedrock reads
// PNG, JPEG, GIF and WebP only) all get one format:
//   - any format sharp can read: JPEG, PNG, WebP, GIF, AVIF, TIFF
//   - turned upright using the camera's orientation flag
//   - scaled to fit MAX_SIDE px (phone photos are often 12-48 MP)
//   - metadata removed, including EXIF GPS coordinates (often the reporter's home)
// The web app converts HEIC/HEIF (iPhone) and BMP in the browser before uploading, since the
// prebuilt sharp can't decode those.
const MAX_SIDE = 2048
const QUALITY = 82
const MAX_INPUT_PIXELS = 120_000_000

export class PhotoError extends Error {
  constructor(message) {
    super(message)
    this.status = 400
  }
}

let sharpLib
async function loadSharp() {
  if (sharpLib === undefined) {
    try {
      sharpLib = (await import('sharp')).default
    } catch (err) {
      console.warn(`[photos] sharp is not available (${err.message}); photos are stored as uploaded, PNG/JPEG/WebP/GIF only.`)
      sharpLib = null
    }
  }
  return sharpLib
}

const PASSTHROUGH = { png: 'image/png', jpeg: 'image/jpeg', webp: 'image/webp', gif: 'image/gif' }
const SUPPORTED = 'JPEG, PNG, WebP, GIF, AVIF, TIFF or HEIC'
const HEIC_HINT = 'This HEIC photo could not be converted here. Upload it from the CityCare website, which converts it, or export it as JPEG.'

/** Decode a data URL. Returns { declared, bytes } or throws PhotoError. */
export function parseDataUrl(dataUrl) {
  const m = /^data:([\w.+-]+\/[\w.+-]+)?(;[^,]*)?;base64,([A-Za-z0-9+/=\s]+)$/.exec(String(dataUrl || ''))
  if (!m) throw new PhotoError('The photo could not be read. Attach it again.')
  const bytes = Buffer.from(m[3], 'base64')
  if (!bytes.length) throw new PhotoError('The photo is empty.')
  return { declared: (m[1] || '').toLowerCase(), bytes }
}

const isHeic = (bytes, declared) => /hei[cf]/.test(declared) || /^ftyp(heic|heix|hevc|hevx|heim|heis|mif1|msf1)/.test(bytes.subarray(4, 12).toString('latin1'))

/**
 * Turn uploaded image bytes into a stored photo: { bytes, mime, ext, width, height }.
 * Throws PhotoError with a message for the resident when the file isn't a usable image.
 */
export async function normalizePhoto(bytes, declared = '') {
  const sharp = await loadSharp()
  if (!sharp) {
    const fmt = Object.keys(PASSTHROUGH).find((k) => declared === PASSTHROUGH[k] || (k === 'jpeg' && declared === 'image/jpg'))
    if (!fmt) throw new PhotoError('Photo must be a PNG, JPEG, WebP or GIF image.')
    return { bytes, mime: PASSTHROUGH[fmt], ext: fmt === 'jpeg' ? 'jpg' : fmt }
  }
  let meta
  try {
    meta = await sharp(bytes, { limitInputPixels: MAX_INPUT_PIXELS }).metadata()
  } catch {
    if (isHeic(bytes, declared)) throw new PhotoError(HEIC_HINT)
    throw new PhotoError(`That file isn't an image we can read. Use a ${SUPPORTED} photo.`)
  }
  // SVG is a document, not a photo, and can carry scripts: refuse it.
  if (meta.format === 'svg') throw new PhotoError(`SVG files aren't accepted. Use a ${SUPPORTED} photo.`)
  try {
    const { data, info } = await sharp(bytes, { limitInputPixels: MAX_INPUT_PIXELS, animated: false })
      .rotate() // apply the EXIF orientation, then drop it with the rest of the metadata
      .resize({ width: MAX_SIDE, height: MAX_SIDE, fit: 'inside', withoutEnlargement: true })
      .flatten({ background: '#ffffff' }) // transparent PNG/WebP areas become white, not black
      .jpeg({ quality: QUALITY, mozjpeg: true })
      .toBuffer({ resolveWithObject: true })
    return { bytes: data, mime: 'image/jpeg', ext: 'jpg', width: info.width, height: info.height }
  } catch (err) {
    if (/pixel limit/i.test(err.message)) throw new PhotoError('That photo is too large. Use one under 120 megapixels.')
    // sharp reads HEIC headers but the prebuilt library can't decode HEVC images.
    if (meta.format === 'heif' && meta.compression !== 'av1') throw new PhotoError(HEIC_HINT)
    throw new PhotoError(`The photo could not be processed. Use a ${SUPPORTED} photo.`)
  }
}
