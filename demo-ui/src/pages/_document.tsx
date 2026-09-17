import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en" data-carbon-theme="g100">
      <Head>
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <meta name="description" content="watsonx.data on IBM Power — Presales Demo" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}
