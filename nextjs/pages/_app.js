import Head from "next/head";
import { Toaster } from "sonner";

import { AuthProvider } from "@/lib/auth";
import "@/styles/globals.css";

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Head>
        <title>Match Up | Book any court, any sport</title>
        <meta
          name="description"
          content="Book any court, any sport. Badminton is open now in 30-minute slots, with football and basketball coming soon. Go Pro for 10% off, longer booking windows and free cancellation."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Component {...pageProps} />
      <Toaster richColors position="top-right" />
    </AuthProvider>
  );
}
