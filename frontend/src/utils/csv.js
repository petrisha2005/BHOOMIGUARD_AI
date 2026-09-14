export function parseCsv(text) {
  const rows = []
  let row = []
  let value = ''
  let quoted = false

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index]
    if (character === '"') {
      if (quoted && text[index + 1] === '"') { value += '"'; index += 1 } else quoted = !quoted
    } else if (character === ',' && !quoted) { row.push(value); value = ''
    } else if ((character === '\n' || character === '\r') && !quoted) {
      if (character === '\r' && text[index + 1] === '\n') index += 1
      row.push(value); rows.push(row); row = []; value = ''
    } else value += character
  }
  if (value || row.length) { row.push(value); rows.push(row) }
  if (!rows.length) return { headers: [], rows: [] }

  const headers = rows[0].map((header) => header.trim())
  const invalidHeaders = headers.length === 0 || headers.some((header) => !header)
  if (invalidHeaders) throw new Error('The CSV header row contains an empty column name.')
  return {
    headers,
    rows: rows.slice(1).filter((cells) => cells.some((cell) => cell.trim())).map((cells) => Object.fromEntries(headers.map((header, index) => [header, (cells[index] || '').trim()]))),
  }
}
