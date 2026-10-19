(function () {
    const hero = document.getElementById('hero-section');
    const canvas = document.getElementById('heroFrames');
    if (!hero || !canvas) return;

    /* ---- Tune here (layout values kept identical to before) ---- */
    const ZOOM = 0.9;        // 1 = frame fits the hero. Smaller = smaller dog
    const ALIGN_X = 1.5;     // 0 = left, 0.5 = center, 1 = right
    const ALIGN_Y = 1;       // 1 = bottom, 0.5 = middle
    const SPRITE = '../assets/hero-sprite.jpg?v=5';
    const TOTAL = 60;        // tiles in the sprite (one horizontal row)
    const LEFT_FRAME = 5;    // dog looking left  (cursor at hero's left edge)
    const IDLE_FRAME = 32;   // calm front-facing pose (cursor at center / pointer away)
    const RIGHT_FRAME = 57;  // dog glancing right (cursor at hero's right edge)
    const FOLLOW = 20;       // higher = snappier tracking
    const RETURN = 10;        // higher = faster return to idle
    /* ------------------------------------------------------------ */

    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ctx = canvas.getContext('2d');

    let sprite = null, ready = false, fw = 0, fh = 0, tw = 0;
    const tx = (i) => Math.round(i * fw);          // left edge of tile i (whole pixels)
    let pos = IDLE_FRAME, target = IDLE_FRAME, rate = RETURN;
    let running = false, lastT = null;
    let fx = 0, fy = 0, fwPx = 0, fhPx = 0;   // frame rect inside the backdrop canvas
    const BK = 0.25;                          // backdrop is blurred anyway, so draw it small
    let lastBack = -1;

    // soft edge fade into the background
    const fade = 'linear-gradient(to right, transparent, #000 13%, #000 87%, transparent), linear-gradient(to bottom, transparent, #000 16%)';
    canvas.style.webkitMaskImage = fade;
    canvas.style.maskImage = fade;
    canvas.style.webkitMaskComposite = 'source-in';
    canvas.style.maskComposite = 'intersect';

    // backdrop: the frame's own edge pixels stretched outward, so the area
    // around the frame matches it (no ghost dog, no visible rectangle)
    const back = document.createElement('canvas');
    back.setAttribute('aria-hidden', 'true');
    back.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;z-index:-4;pointer-events:none;filter:blur(22px)';
    const PAD = 60;                                   // overscan (css px) so blur never shows an edge
    hero.insertBefore(back, canvas);
    const bctx = back.getContext('2d');

    function smooth(g) {
        g.imageSmoothingEnabled = true;
        g.imageSmoothingQuality = 'high';
    }

    // average colour of a strip of the frame, shrunk to tw x th tiny pixels
    const tmp = document.createElement('canvas');
    const tctx = tmp.getContext('2d');
    function strip(sx, sy, sw, sh, tw, th) {
        tmp.width = tw; tmp.height = th;
        tctx.imageSmoothingEnabled = true;
        tctx.imageSmoothingQuality = 'high';
        tctx.drawImage(sprite, sx, sy, sw, sh, 0, 0, tw, th);
        return tmp;
    }

    function drawBackdrop(i) {
        if (i === lastBack) return;
        lastBack = i;
        const sx = tx(i), W = back.width, H = back.height;
        const r = fx + fwPx, b = fy + fhPx;
        bctx.clearRect(0, 0, W, H);
        bctx.imageSmoothingEnabled = true;
        bctx.imageSmoothingQuality = 'high';
        // each side is a smooth colour gradient taken from the frame's own edge
        if (fx > 0) bctx.drawImage(strip(sx, 0, 6, fh, 1, 6), 0, 0, 1, 6, 0, fy, fx, fhPx);
        if (r < W)  bctx.drawImage(strip(sx + tw - 6, 0, 6, fh, 1, 6), 0, 0, 1, 6, r, fy, W - r, fhPx);
        if (fy > 0) {
            bctx.drawImage(strip(sx, 0, tw, 6, 6, 1), 0, 0, 6, 1, fx, 0, fwPx, fy);
            if (fx > 0) bctx.drawImage(strip(sx, 0, 6, 6, 1, 1), 0, 0, 1, 1, 0, 0, fx, fy);
            if (r < W)  bctx.drawImage(strip(sx + tw - 6, 0, 6, 6, 1, 1), 0, 0, 1, 1, r, 0, W - r, fy);
        }
        bctx.drawImage(sprite, sx, 0, tw, fh, fx, fy, fwPx, fhPx);                          // the frame itself
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
        if (f > 0.001 && i < TOTAL - 1) {          // blend toward next frame
            ctx.globalAlpha = f;
            ctx.drawImage(sprite, tx(i + 1), 0, tw, fh, 0, 0, canvas.width, canvas.height);
            ctx.globalAlpha = 1;
        }
        drawBackdrop(i);
    }

    function layout() {
        if (!ready) return;
        const W = hero.clientWidth, H = hero.clientHeight;
        const dpr = 1;
        const s = Math.min(W / tw, H / fh) * ZOOM;
        const w = tw * s, h = fh * s;
        const left = (W - w) * ALIGN_X, top = (H - h) * ALIGN_Y;

        canvas.style.inset = 'auto';
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
        smooth(ctx); smooth(bctx);                 // resizing a canvas resets these

        fx = Math.round((left + PAD) * BK); fy = Math.round((top + PAD) * BK);
        fwPx = Math.round(w * BK); fhPx = Math.round(h * BK);
        lastBack = -1;
        render();
    }

    // frame-rate independent exponential easing toward the target frame
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
        tw = Math.floor(fw) - (fw % 1 ? 1 : 0);   // stay 1px inside the tile if it is fractional
        ready = true;
        const staticImg = hero.querySelector('.hero-animal');   // hide static dog, animated one replaces it
        if (staticImg) staticImg.style.display = 'none';
        layout();
    };
    sprite.onerror = () => {
        console.error('hero-tracking: could not load sprite -> ' + sprite.src +
            ' (check the path in SPRITE and that the file is in assets/)');
    };
    sprite.src = SPRITE;

    if (!reduce) {
        hero.addEventListener('pointermove', (e) => {
            if (e.pointerType === 'touch') return;
            if (document.querySelector('.auth-modal.is-open')) return idle();
            go(frameFor(e.clientX), FOLLOW);
        });
        hero.addEventListener('pointerleave', idle);
        window.addEventListener('blur', idle);
        document.addEventListener('visibilitychange', () => { if (document.hidden) idle(); });
    }

    window.addEventListener('resize', layout);
})();


/* ==================================================================
 * FEATURES SECTION - same hero sprite, left side, follows the cursor
 * (HTML me koi change nahi: canvas apne aap .features-visual me lag jata hai)
 * ================================================================== */
(function () {
    const section = document.getElementById('features-section');
    const holder = section && section.querySelector('.features-visual');
    if (!section || !holder) return;

    /* ---- Tune here ---- */
    const SPRITE = '../assets/hero-sprite.jpg?v=5';   // hero wale sprite jaisa hi path rakho
    const TOTAL = 60;
    const LEFT_FRAME = 5;      // kutta left dekhe
    const IDLE_FRAME = 32;     // seedha front
    const RIGHT_FRAME = 57;    // kutta right dekhe
    const FOLLOW = 20;         // higher = snappier tracking
    const RETURN = 10;         // higher = faster return to idle
    const SIZE = 1.15;         // kutte ka size (holder ki height ka multiple). Chhota = smaller dog
    const OFFSET_X = 0;        // px: - left, + right
    const OFFSET_Y = 0;        // px: - up,   + down
    const TURN_RANGE = 0.45;   // cursor kutte se section-width ka itna door ho to poora mud jaye
    const HIDE_OLD_IMAGE = true;   // purani puppy image (feature-section.png) hide karni hai?
    /* ------------------ */

    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.cssText = 'position:absolute;left:50%;top:50%;pointer-events:none;z-index:1;';
    // soft round fade: peach frame section ke background me ghul jata hai
    const fade = 'radial-gradient(ellipse 50% 50% at 50% 50%, #000 52%, rgba(0,0,0,.55) 74%, transparent 100%)';
    canvas.style.webkitMaskImage = fade;
    canvas.style.maskImage = fade;
    holder.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    let sprite = null, ready = false, fw = 0, fh = 0, tw = 0;
    const tx = (i) => Math.round(i * fw);
    let pos = IDLE_FRAME, target = IDLE_FRAME, rate = RETURN;
    let running = false, lastT = null;

    function render() {
        if (!ready) return;
        const p = Math.min(Math.max(pos, 0), TOTAL - 1);
        const i = Math.floor(p), f = p - i;
        ctx.globalAlpha = 1;
        ctx.drawImage(sprite, tx(i), 0, tw, fh, 0, 0, canvas.width, canvas.height);
        if (f > 0.001 && i < TOTAL - 1) {
            ctx.globalAlpha = f;
            ctx.drawImage(sprite, tx(i + 1), 0, tw, fh, 0, 0, canvas.width, canvas.height);
            ctx.globalAlpha = 1;
        }
    }

    function layout() {
        if (!ready) return;
        const H = holder.clientHeight || section.clientHeight * 0.72;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const s = (H / fh) * SIZE;
        const w = tw * s, h = fh * s;
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';
        canvas.style.transform = `translate(calc(-50% + ${OFFSET_X}px), calc(-50% + ${OFFSET_Y}px))`;
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        render();
    }

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

    // cursor kutte ke left me -> left dekhe, right me -> right dekhe
    function frameFor(clientX) {
        const r = canvas.getBoundingClientRect();
        const cx = r.left + r.width / 2;
        const d = Math.min(Math.max((clientX - cx) / (section.clientWidth * TURN_RANGE), -1), 1);
        const n = (d + 1) / 2;
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
        if (HIDE_OLD_IMAGE) {
            const old = holder.querySelector('img');
            if (old) old.style.display = 'none';
        }
        layout();
    };
    sprite.onerror = () => {
        console.error('features-tracking: could not load sprite -> ' + sprite.src);
        canvas.remove();          // sprite na mile to purani puppy image hi dikhti rahe
    };
    sprite.src = SPRITE;

    if (!reduce) {
        section.addEventListener('pointermove', (e) => {
            if (e.pointerType === 'touch') return;
            if (document.querySelector('.auth-modal.is-open')) return idle();
            go(frameFor(e.clientX), FOLLOW);
        });
        section.addEventListener('pointerleave', idle);
        window.addEventListener('blur', idle);
        document.addEventListener('visibilitychange', () => { if (document.hidden) idle(); });
    }

    window.addEventListener('resize', layout);
})();