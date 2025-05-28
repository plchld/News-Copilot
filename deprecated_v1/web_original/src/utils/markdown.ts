export function convertMarkdownToHtml(markdown: string): string {
  if (!markdown) return ''
  
  let html = markdown
    // H2 Headers
    .replace(/^## (.+)$/gm, '<h2 class="mt-6 mb-4 text-gray-800 font-semibold text-xl border-b-2 border-gray-200 pb-2">$1</h2>')
    // H3 Headers  
    .replace(/^### (.+)$/gm, '<h3 class="mt-5 mb-3 text-gray-800 font-semibold text-lg">$1</h3>')
    // H4 Headers
    .replace(/^#### (.+)$/gm, '<h4 class="mt-4 mb-2 text-gray-700 font-semibold text-base">$1</h4>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-gray-700 font-semibold">$1</strong>')
    // Italic (avoid conflicts with bold)
    .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em class="text-gray-600">$1</em>')
  
  // Process lists before paragraphs to avoid conflicts
  const lines = html.split('\n')
  let inList = false
  let processedLines = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmedLine = line.trim()
    
    // Check if it's a list item
    if (trimmedLine.startsWith('- ')) {
      if (!inList) {
        processedLines.push('<ul class="list-disc list-inside ml-4 my-3 space-y-2">')
        inList = true
      }
      processedLines.push(`<li class="text-gray-700">${trimmedLine.substring(2)}</li>`)
    } else {
      // Close list if we were in one
      if (inList && trimmedLine !== '') {
        processedLines.push('</ul>')
        inList = false
      }
      processedLines.push(line)
    }
  }
  
  // Close list if still open at end
  if (inList) {
    processedLines.push('</ul>')
  }
  
  html = processedLines.join('\n')
  
  // Now handle paragraphs
  html = html
    // Paragraphs (but not within lists or headers)
    .replace(/\n\n+/g, '</p><p class="my-3 leading-relaxed">')
    // Single line breaks (but not in lists)
    .replace(/\n(?!<\/?(ul|li|h[234]>))/g, '<br>')
  
  // Wrap in paragraph if needed
  if (!html.includes('<p>') && !html.match(/<(h[234]|ul)>/)) {
    html = `<p class="my-3 leading-relaxed">${html}</p>`
  } else if (html.match(/<(h[234]|ul)>/) && !html.match(/^<(h[234]|ul|p)>/)) {
    // Start with paragraph if doesn't start with header/list/p
    const firstTag = html.match(/<(h[234]|ul|p)>/)
    if (firstTag) {
      const index = html.indexOf(firstTag[0])
      html = `<p class="my-3 leading-relaxed">${html.substring(0, index)}</p>${html.substring(index)}`
    }
  }
  
  // Clean up empty paragraphs
  html = html.replace(/<p[^>]*>(\s|<br>)*<\/p>/g, '')
  
  return html
}