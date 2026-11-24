package jo.hakawati.hq;

import android.service.dreams.DreamService;
import android.webkit.WebView;

/** Screensaver ("daydream") that shows the same team HQ page. */
public class HqDream extends DreamService {
    private WebView web;

    @Override
    public void onAttachedToWindow() {
        super.onAttachedToWindow();
        setInteractive(false);
        setFullscreen(true);
        setScreenBright(true);
        web = Hq.create(this);
        setContentView(web);
    }

    @Override
    public void onDetachedFromWindow() {
        if (web != null) { web.destroy(); web = null; }
        super.onDetachedFromWindow();
    }
}
