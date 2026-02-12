import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'رادار جنگ شناختی',
  description: 'رادار تحلیل جنگ شناختی - سیستم تحلیل و پایش اخبار',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <link
          href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css"
          rel="stylesheet"
          type="text/css"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
