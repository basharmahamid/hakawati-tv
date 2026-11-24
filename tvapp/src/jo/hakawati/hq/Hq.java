package jo.hakawati.hq;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/** Builds the full-screen WebView that shows the team HQ page. Shared by the app and the screensaver. */
final class Hq {
    static final String URL = "https://basharmahamid.github.io/hakawati-tv/?lite=1";

    static WebView create(Context c) {
        final WebView w = new WebView(c);
        w.setBackgroundColor(Color.rgb(11, 15, 26));
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        final Handler h = new Handler(Looper.getMainLooper());
        w.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {
                // No network yet (TV just woke up): try the page again in 20 seconds.
                if (r.isForMainFrame()) h.postDelayed(new Runnable() { public void run() { w.loadUrl(URL); } }, 20000);
            }
        });
        w.setWebChromeClient(new WebChromeClient() {
            @Override
            public Bitmap getDefaultVideoPoster() {
                // Hide WebView's grey "play" placeholder that flashes before a video's first frame.
                return Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888);
            }
        });
        w.loadUrl(URL);
        return w;
    }
}
