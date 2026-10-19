/* PawAI dashboard - hero cursor tracking
 * HTML me koi change nahi chahiye: ye file khud canvas + backdrop + shade banati hai
 * aur purani <img class="hero-animal"> ko hide kar deti hai.
 */
(function () {
    function start() {
        const hero = document.getElementById('hero-section');
        if (!hero || hero.dataset.heroTracking) return;
        hero.dataset.heroTracking = '1';

        /* ---- Tune here ---- */
        const SPRITE = '../assets/hero-sprite-beagle.jpg?v=2';
        const TOTAL = 72;          // tiles in the sprite (one horizontal row)
        const LEFT_FRAME = 2;      // cursor at hero's left edge  (dog looks left)
        const IDLE_FRAME = 22;     // calm looking-up pose (cursor at center / pointer away)
        const RIGHT_FRAME = 68;    // cursor at hero's right edge (dog turns to face front)
        const FOLLOW = 8;         // higher = snappier tracking
        const RETURN = 4;         // higher = faster return to idle
        const ZOOM = 0.92;         // 1 = frame fits the hero. Smaller = smaller dog
        const ALIGN_X = 0.85;         // 0 = left, 0.5 = center, 1 = right
        const ALIGN_Y = 1;         // 1 = bottom, 0.5 = middle
        const MOBILE_MAX = 760;    // px
        const MOBILE_HEIGHT = 0.5; // on phones the frame takes this share of the hero height
        /* ------------------- */

        const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

        // page ka purana static image hide (HTML untouched)
        const st = document.createElement('style');
        st.textContent = `
            #hero-section .hero-animal{display:none !important}
            #hero-section .hero-shade{
                position:absolute;inset:0;z-index:1;pointer-events:none;
                background:linear-gradient(90deg,
                    rgba(24,20,18,.97) 0%, rgba(24,20,18,.93) 38%,
                    rgba(24,20,18,.58) 55%, rgba(24,20,18,.14) 68%, rgba(24,20,18,0) 78%);
                transition:opacity .55s ease;
            }
            body.light-theme #hero-section .hero-shade,
            html[data-theme="light"] #hero-section .hero-shade,
            body[data-theme="light"] #hero-section .hero-shade{opacity:0}
            @media (max-width:${MOBILE_MAX}px){
                #hero-section .hero-shade{
                    background:linear-gradient(180deg,
                        rgba(24,20,18,.94) 0%, rgba(24,20,18,.82) 50%, rgba(24,20,18,.25) 100%);
                }
            }
        `;
        document.head.appendChild(st);

        const shade = document.createElement('div');
        shade.className = 'hero-shade';
        shade.setAttribute('aria-hidden', 'true');

        const canvas = document.createElement('canvas');
        canvas.id = 'heroFrames';
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', 'PawAI pet companion');
        canvas.style.cssText = 'position:absolute;z-index:0;pointer-events:none';
        const ctx = canvas.getContext('2d');

        let sprite = null, ready = false, fw = 0, fh = 0, tw = 0;
        const tx = (i) => Math.round(i * fw);
        let pos = IDLE_FRAME, target = IDLE_FRAME, rate = RETURN;
        let running = false, lastT = null;
        let fx = 0, fy = 0, fwPx = 0, fhPx = 0;
        const BK = 0.25;
        let lastBack = -1;

        // soft edge fade into the backdrop
        const fade = 'linear-gradient(to right, transparent, #000 13%, #000 94%, transparent), linear-gradient(to bottom, transparent, #000 16%)';
        canvas.style.webkitMaskImage = fade;
        canvas.style.maskImage = fade;
        canvas.style.webkitMaskComposite = 'source-in';
        canvas.style.maskComposite = 'intersect';

        // backdrop: frame ke edge pixels bahar tak stretch, taaki frame ke aas-paas ka
        // area frame se match kare (koi rectangle nahi dikhta)
        const back = document.createElement('canvas');
        back.setAttribute('aria-hidden', 'true');
        back.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;z-index:-4;pointer-events:none;filter:blur(22px)';
        const PAD = 60;
        const bctx = back.getContext('2d');

        hero.insertBefore(back, hero.firstChild);
        hero.insertBefore(canvas, back.nextSibling);
        hero.insertBefore(shade, canvas.nextSibling);

        function smooth(g) {
            g.imageSmoothingEnabled = true;
            g.imageSmoothingQuality = 'high';
        }

        const tmp = document.createElement('canvas');
        const tctx = tmp.getContext('2d');
        function strip(sx, sy, sw, sh, w, h) {
            tmp.width = w; tmp.height = h;
            tctx.imageSmoothingEnabled = true;
            tctx.imageSmoothingQuality = 'high';
            tctx.drawImage(sprite, sx, sy, sw, sh, 0, 0, w, h);
            return tmp;
        }

        function drawBackdrop(i) {
            if (i === lastBack) return;
            lastBack = i;
            const sx = tx(i), W = back.width, H = back.height;
            const r = fx + fwPx, b = fy + fhPx;
            bctx.clearRect(0, 0, W, H);
            smooth(bctx);
            if (fx > 0) bctx.drawImage(strip(sx, 0, 6, fh, 1, 6), 0, 0, 1, 6, 0, fy, fx, fhPx);
            if (r < W)  bctx.drawImage(strip(sx + tw - 6, 0, 6, fh, 1, 6), 0, 0, 1, 6, r, fy, W - r, fhPx);
            if (fy > 0) {
                bctx.drawImage(strip(sx, 0, tw, 6, 6, 1), 0, 0, 6, 1, fx, 0, fwPx, fy);
                if (fx > 0) bctx.drawImage(strip(sx, 0, 6, 6, 1, 1), 0, 0, 1, 1, 0, 0, fx, fy);
                if (r < W)  bctx.drawImage(strip(sx + tw - 6, 0, 6, 6, 1, 1), 0, 0, 1, 1, r, 0, W - r, fy);
            }
            bctx.drawImage(sprite, sx, 0, tw, fh, fx, fy, fwPx, fhPx);
            if (b < H) {
                bctx.drawImage(strip(sx, fh - 6, tw, 6, 6, 1), 0, 0, 6, 1, fx, b, fwPx, H - b);
                if (fx > 0) bctx.drawImage(strip(sx, fh - 6, 6, 6, 1, 1), 0, 0, 1, 1, 0, b, fx, H - b);
                if (r < W)  bctx.drawImage(strip(sx + tw - 6, fh - 6, 6, 6, 1, 1), 0, 0, 1, 1, r, b, W - r, H - b);
            }
        }

        function render() {
            if (!ready) return;
            const p = Math.min(Math.max(pos, 0), TOTAL - 1);
            const i = Math.floor(p), f = p - i;

            ctx.globalAlpha = 1;
            ctx.drawImage(sprite, tx(i), 0, tw, fh, 0, 0, canvas.width, canvas.height);
            if (f > 0.001 && i < TOTAL - 1) {          // neighbouring tiles almost identical -> no ghosting
                ctx.globalAlpha = f;
                ctx.drawImage(sprite, tx(i + 1), 0, tw, fh, 0, 0, canvas.width, canvas.height);
                ctx.globalAlpha = 1;
            }
            drawBackdrop(i);
        }

        function layout() {
            if (!ready) return;
            const W = hero.clientWidth, H = hero.clientHeight;
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            const mobile = W <= MOBILE_MAX;
            const s = mobile
                ? (H * MOBILE_HEIGHT) / fh
                : Math.min(W / tw, H / fh) * ZOOM;
            const w = tw * s, h = fh * s;
            const left = (W - w) * ALIGN_X, top = (H - h) * ALIGN_Y;

            canvas.style.left = left + 'px';
            canvas.style.top = top + 'px';
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';
            canvas.width = Math.round(w * dpr);
            canvas.height = Math.round(h * dpr);
            back.style.inset = 'auto';
            back.style.left = -PAD + 'px';
            back.style.top = -PAD + 'px';
            back.style.width = (W + PAD * 2) + 'px';
            back.style.height = (H + PAD * 2) + 'px';
            back.width = Math.round((W + PAD * 2) * BK);
            back.height = Math.round((H + PAD * 2) * BK);
            smooth(ctx); smooth(bctx);

            fx = Math.round((left + PAD) * BK); fy = Math.round((top + PAD) * BK);
            fwPx = Math.round(w * BK); fhPx = Math.round(h * BK);
            lastBack = -1;
            render();
        }

        // frame-rate independent easing toward the target frame
        function loop(t) {
            if (!running) return;
            if (lastT === null) lastT = t;
            const dt = Math.min((t - lastT) / 1000, 0.05);
            lastT = t;
            pos += (target - pos) * (1 - Math.exp(-rate * dt));
            if (Math.abs(target - pos) < 0.01) {
                pos = target; running = false; lastT = null; render(); return;
            }
            render();
            requestAnimationFrame(loop);
        }

        function go(to, r) {
            target = to; rate = r;
            if (!running && ready) { running = true; lastT = null; requestAnimationFrame(loop); }
        }

        // cursor X across the hero -> frame index (left / idle / right anchors)
        function frameFor(clientX) {
            const r = hero.getBoundingClientRect();
            const n = Math.min(Math.max((clientX - r.left) / r.width, 0), 1);
            return n < 0.5
                ? LEFT_FRAME + (IDLE_FRAME - LEFT_FRAME) * (n / 0.5)
                : IDLE_FRAME + (RIGHT_FRAME - IDLE_FRAME) * ((n - 0.5) / 0.5);
        }

        const idle = () => go(IDLE_FRAME, RETURN);

        sprite = new Image();
        sprite.onload = () => {
            fw = sprite.naturalWidth / TOTAL;
            fh = sprite.naturalHeight;
            tw = Math.floor(fw) - (fw % 1 ? 1 : 0);
            ready = true;
            layout();
        };
        sprite.onerror = () => {
            console.error('hero-tracking: could not load sprite -> ' + sprite.src +
                ' (check the path in SPRITE and that the file is in assets/)');
            // sprite na mile to purana static image wapas dikha do
            st.textContent = st.textContent.replace('#hero-section .hero-animal{display:none !important}', '');
            canvas.remove(); back.remove(); shade.remove();
        };
        sprite.src = SPRITE;

        if (!reduce) {
            hero.addEventListener('pointermove', (e) => {
                if (e.pointerType === 'touch') return;
                go(frameFor(e.clientX), FOLLOW);
            });
            hero.addEventListener('pointerleave', idle);
            window.addEventListener('blur', idle);
            document.addEventListener('visibilitychange', () => { if (document.hidden) idle(); });
        }

        window.addEventListener('resize', layout);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
    else start();
})();