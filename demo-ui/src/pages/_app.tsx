import type { AppProps } from 'next/app'
import { AudienceProvider, AudienceSelector } from '../context/AudienceContext'
import '../styles/globals.scss'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AudienceProvider>
      <Component {...pageProps} />
      <AudienceSelector />
    </AudienceProvider>
  )
}
