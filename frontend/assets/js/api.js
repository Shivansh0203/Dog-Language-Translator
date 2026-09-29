/**
 * PawAI frontend API helper.
 *
 * Talks to the PawAI FastAPI backend using the server-side, HttpOnly
 * session cookie described in backend/app/core/security.py. There is no
 * JWT and no token of any kind stored in JavaScript-land: every request
 * is sent with credentials: "include" so the browser attaches/receives
 * the `pawai_session` cookie automatically, and every response is read
 * to decide what happened - nothing is ever written to localStorage or
 * sessionStorage for authentication purposes.
 *
 * Include this file on every page that talks to the backend, before any
 * page-specific <script>:
 *   <script src="assets/js/api.js"></script>
 */
(function (global) {
  // const isNestedFrontendPage = global.location.pathname.includes("/dog/");
  // const frontendAssetPrefix = isNestedFrontendPage ? "../assets" : "assets";

  // // UI preferences are intentionally separate from authentication. This
  // // key contains colors and accessibility choices only; sessions remain in
  // // the server-issued HttpOnly cookie and are never readable by JavaScript.
  // const THEME_PREFERENCES_KEY = "pawai.preferences.v1";
  // const defaultThemePreferences = {
  //   theme: "dark",
  //   fontSize: "medium",
  //   largerText: true,
  //   highContrast: false,
  //   reduceAnimations: false,
  //   customColors: null
  // };
  // const basePalettes = {
  //   dark: {
  //     background: "#090a10",
  //     panel: "#141218",
  //     primary: "#ff3d91",
  //     accent: "#ff5aa4",
  //     text: "#f8f5fa",
  //     button: "#ff3d91"
  //   },
  //   light: {
  //     background: "#fffafd",
  //     panel: "#ffffff",
  //     primary: "#d91f75",
  //     accent: "#ff5aa4",
  //     text: "#241b25",
  //     button: "#df287b"
  //   }
  // };

  // function validHex(value) {
  //   return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);
  // }

  // function hexToRgb(hex) {
  //   const value = hex.slice(1);
  //   return [0, 2, 4].map((offset) => parseInt(value.slice(offset, offset + 2), 16));
  // }

  // function mix(hex, target, amount) {
  //   const [r1, g1, b1] = hexToRgb(hex);
  //   const [r2, g2, b2] = hexToRgb(target);
  //   const channel = (first, second) => Math.round(first + (second - first) * amount).toString(16).padStart(2, "0");
  //   return `#${channel(r1, r2)}${channel(g1, g2)}${channel(b1, b2)}`;
  // }

  // function relativeLuminance(hex) {
  //   const channels = hexToRgb(hex).map((value) => {
  //     const normalized = value / 255;
  //     return normalized <= .03928 ? normalized / 12.92 : ((normalized + .055) / 1.055) ** 2.4;
  //   });
  //   return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2];
  // }

  // function contrastRatio(first, second) {
  //   const [lighter, darker] = [relativeLuminance(first), relativeLuminance(second)].sort((a, b) => b - a);
  //   return (lighter + .05) / (darker + .05);
  // }

  // function readThemePreferences() {
  //   try {
  //     const saved = JSON.parse(global.localStorage.getItem(THEME_PREFERENCES_KEY) || "{}");
  //     return { ...defaultThemePreferences, ...saved };
  //   } catch (error) {
  //     return { ...defaultThemePreferences };
  //   }
  // }

  // function saveThemePreferences(preferences) {
  //   global.localStorage.setItem(THEME_PREFERENCES_KEY, JSON.stringify(preferences));
  // }

  // function resolvedTheme(theme) {
  //   if (theme !== "system") return theme === "light" ? "light" : "dark";
  //   return global.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  // }

  // function paletteFor(preferences) {
  //   const palette = { ...basePalettes[resolvedTheme(preferences.theme)] };
  //   if (preferences.customColors && typeof preferences.customColors === "object") {
  //     Object.entries(palette).forEach(([key]) => {
  //       if (validHex(preferences.customColors[key])) palette[key] = preferences.customColors[key];
  //     });
  //   }
  //   return palette;
  // }

  // function installThemeStyles() {
  //   if (document.querySelector("#pawai-shared-theme")) return;
  //   const style = document.createElement("style");
  //   style.id = "pawai-shared-theme";
  //   style.textContent = `
  //     html[data-pawai-theme-active] body {
  //       position: relative;
  //       isolation: isolate;
  //       color: var(--text) !important;
  //       background: radial-gradient(circle at 78% 8%, var(--pawai-primary-glow), transparent 34rem),
  //         radial-gradient(circle at 12% 90%, var(--pawai-accent-glow), transparent 26rem),
  //         var(--pawai-page-background) !important;
  //     }
  //     html[data-pawai-theme-active] body::before,
  //     html[data-pawai-theme-active] body::after {
  //       content: "";
  //       position: fixed;
  //       z-index: 0;
  //       inset: -160px;
  //       pointer-events: none;
  //       background: var(--primary);
  //       opacity: .075;
  //       -webkit-mask-image: url("${frontendAssetPrefix}/paw-print.svg");
  //       -webkit-mask-repeat: repeat;
  //       -webkit-mask-position: 0 0;
  //       -webkit-mask-size: 156px 156px;
  //       mask-image: url("${frontendAssetPrefix}/paw-print.svg");
  //       mask-repeat: repeat;
  //       mask-position: 0 0;
  //       mask-size: 156px 156px;
  //       animation: pawai-paw-drift 28s linear infinite;
  //     }
  //     html[data-pawai-theme-active] body > * { position: relative; z-index: 1; }
  //     html[data-pawai-theme-active] body::after {
  //       background: var(--accent);
  //       opacity: .045;
  //       -webkit-mask-size: 226px 226px;
  //       mask-size: 226px 226px;
  //       animation-name: pawai-paw-float;
  //       animation-duration: 39s;
  //     }
  //     @keyframes pawai-paw-drift { to { -webkit-mask-position: 380px 260px; mask-position: 380px 260px; } }
  //     @keyframes pawai-paw-float { to { -webkit-mask-position: -300px 210px; mask-position: -300px 210px; } }
  //     html[data-pawai-theme-active] .card, html[data-pawai-theme-active] .panel, html[data-pawai-theme-active] .navbar,
  //     html[data-pawai-theme-active] .bottom-nav, html[data-pawai-theme-active] .floating-card, html[data-pawai-theme-active] .feature,
  //     html[data-pawai-theme-active] .step, html[data-pawai-theme-active] .stat, html[data-pawai-theme-active] .help-item,
  //     html[data-pawai-theme-active] .about-item, html[data-pawai-theme-active] .sidebar, html[data-pawai-theme-active] .chat-panel {
  //       color: var(--text) !important; background: var(--panel) !important; border-color: var(--line) !important;
  //     }
  //     html[data-pawai-theme-active] input:not([type="checkbox"]), html[data-pawai-theme-active] select,
  //     html[data-pawai-theme-active] textarea { color: var(--text) !important; background: var(--field) !important; border-color: var(--line-strong) !important; }
  //     html[data-pawai-theme-active] a:not(.primary-btn):not(.ghost-btn), html[data-pawai-theme-active] .brand-accent,
  //     html[data-pawai-theme-active] .nav-link.active { color: var(--primary) !important; }
  //     html[data-pawai-theme-active] .primary-btn, html[data-pawai-theme-active] .camera-btn,
  //     html[data-pawai-theme-active] .btn-primary { color: var(--button-text) !important; background: var(--button) !important; border-color: var(--button) !important; }
  //     html[data-pawai-theme-active] .ghost-btn, html[data-pawai-theme-active] .btn-ghost {
  //       color: var(--primary) !important; background: var(--pawai-button-soft) !important; border-color: var(--primary) !important;
  //     }
  //     html[data-pawai-theme-active] .switch input:checked + .slider { background: var(--button) !important; }
  //     html[data-pawai-theme-active] .nav-link, html[data-pawai-theme-active] .pill { border-color: var(--primary) !important; }
  //     html[data-pawai-theme-active] .muted, html[data-pawai-theme-active] p { color: var(--muted) !important; }
  //     html[data-pawai-reduce-motion="true"] *, html[data-pawai-reduce-motion="true"] *::before,
  //     html[data-pawai-reduce-motion="true"] *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; scroll-behavior: auto !important; }
  //   `;
  //   document.head.appendChild(style);
  // }

  // function applyTheme(preferences = readThemePreferences()) {
  //   const palette = paletteFor(preferences);
  //   const root = document.documentElement;
  //   const fontScale = preferences.fontSize === "small" ? .78 : preferences.fontSize === "large" ? 1.28 : 1;
  //   const accessibilityScale = preferences.largerText ? 1.12 : 1;
  //   root.dataset.pawaiThemeActive = resolvedTheme(preferences.theme);
  //   root.dataset.pawaiHighContrast = String(Boolean(preferences.highContrast));
  //   root.dataset.pawaiReduceMotion = String(Boolean(preferences.reduceAnimations));
  //   root.style.setProperty("--bg", palette.background);
  //   root.style.setProperty("--panel", palette.panel);
  //   root.style.setProperty("--field", mix(palette.panel, palette.background, .35));
  //   root.style.setProperty("--line", mix(palette.panel, palette.text, .18));
  //   root.style.setProperty("--line-strong", mix(palette.panel, palette.text, .35));
  //   root.style.setProperty("--text", palette.text);
  //   root.style.setProperty("--muted", mix(palette.text, palette.background, .38));
  //   root.style.setProperty("--pink", palette.primary);
  //   root.style.setProperty("--pink-soft", palette.accent);
  //   root.style.setProperty("--primary", palette.primary);
  //   root.style.setProperty("--button", palette.button);
  //   root.style.setProperty("--button-text", contrastRatio("#ffffff", palette.button) >= contrastRatio("#000000", palette.button) ? "#ffffff" : "#000000");
  //   root.style.setProperty("--pawai-page-background", palette.background);
  //   root.style.setProperty("--pawai-panel-tint", mix(palette.panel, palette.primary, .06));
  //   root.style.setProperty("--pawai-button-soft", mix(palette.panel, palette.button, .12));
  //   root.style.setProperty("--pawai-primary-glow", mix(palette.background, palette.primary, .16));
  //   root.style.setProperty("--pawai-accent-glow", mix(palette.background, palette.accent, .1));
  //   root.style.setProperty("--pawai-ui-scale", String(fontScale * accessibilityScale));
  //   root.style.setProperty("zoom", String(fontScale * accessibilityScale));
  //   installThemeStyles();
  //   return palette;
  // }

  // function updateThemePreferences(patch) {
  //   const preferences = { ...readThemePreferences(), ...patch };
  //   saveThemePreferences(preferences);
  //   return { preferences, palette: applyTheme(preferences) };
  // }

  // global.PawAITheme = {
  //   apply: applyTheme,
  //   getPreferences: readThemePreferences,
  //   getPalette() { return paletteFor(readThemePreferences()); },
  //   update: updateThemePreferences,
  //   resetColors() { return updateThemePreferences({ customColors: null }); },
  //   contrastRatio
  // };
  // applyTheme();
  // const colorSchemeQuery = global.matchMedia("(prefers-color-scheme: light)");
  // const refreshSystemTheme = () => {
  //   if (readThemePreferences().theme === "system") applyTheme();
  // };
  // if (typeof colorSchemeQuery.addEventListener === "function") {
  //   colorSchemeQuery.addEventListener("change", refreshSystemTheme);
  // } else if (typeof colorSchemeQuery.addListener === "function") {
  //   colorSchemeQuery.addListener(refreshSystemTheme);
  // }

  // The origin the FastAPI backend is running on. The backend's
  // CORS_ORIGINS (see backend/.env.example) must include the origin this
  // frontend is served from, and allow_credentials must stay true, or the
  // browser will refuse to send/receive the session cookie.
  //
  // Override by setting `window.PAWAI_API_BASE_URL` in a <script> tag
  // before this file loads, e.g. when deploying frontend and backend to
  // different hosts.
  const configuredBase = global.PAWAI_API_BASE_URL;
  const isHttpPage = global.location.protocol === "http:" || global.location.protocol === "https:";
  const isLocalDevFrontend =
    isHttpPage &&
    (global.location.hostname === "localhost" || global.location.hostname === "127.0.0.1") &&
    global.location.port !== "8080";
  const API_BASE_URL = configuredBase !== undefined
    ? String(configuredBase).replace(/\/$/, "")
    // Keep localhost and 127.0.0.1 aligned. They are different sites for
    // SameSite cookies, so changing hosts between the static frontend and
    // API would make the browser omit the HttpOnly session on /auth/me.
    : (isLocalDevFrontend
      ? `http://${global.location.hostname}:8000`
      : (isHttpPage ? global.location.origin : "http://localhost:8000"));

  /**
   * Error thrown for any non-2xx response or network failure.
   * - status 0            -> network/server unreachable (fetch itself threw)
   * - status 401          -> not authenticated / session expired
   * - status 404/409/422… -> whatever the backend returned
   * - fieldErrors         -> array of {field, message} when the backend
   *                          returned a pydantic validation error (422)
   */
  class ApiError extends Error {
    constructor(message, { status = 0, fieldErrors = [], raw = null } = {}) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.fieldErrors = fieldErrors;
      this.raw = raw;
    }

    get isNetworkError() {
      return this.status === 0;
    }

    get isUnauthorized() {
      return this.status === 401;
    }
  }

  // FastAPI/pydantic send validation errors as:
  //   { "detail": [{ "loc": ["body", "email"], "msg": "...", "type": "..." }, ...] }
  // and plain string errors as:
  //   { "detail": "Invalid username/email or password." }
  function parseDetail(detail) {
    if (!detail) return null;

    if (typeof detail === "string") {
      return { message: detail, fieldErrors: [] };
    }

    if (Array.isArray(detail)) {
      const fieldErrors = detail.map((item) => {
        const loc = Array.isArray(item.loc) ? item.loc : [];
        const field = loc.length ? String(loc[loc.length - 1]) : "field";
        return { field, message: item.msg || "Invalid value." };
      });
      const message = fieldErrors
        .map((entry) => (entry.field === "field" ? entry.message : `${entry.field}: ${entry.message}`))
        .join(" ");
      return { message, fieldErrors };
    }

    return null;
  }

  function statusFallbackMessage(status) {
    switch (status) {
      case 401:
        return "Invalid username/email or password.";
      case 404:
        return "Not found.";
      case 409:
        return "That account already exists.";
      case 501:
        return "This feature isn't available yet.";
      case 503:
        return "This feature is not configured yet.";
      default:
        return `Request failed (${status}).`;
    }
  }

  async function request(path, { method = "GET", body, headers } = {}) {
    let response;
    try {
      response = await fetch(`${API_BASE_URL}${path}`, {
        method,
        // Required so the browser sends/stores the HttpOnly session cookie
        // even though the API lives on a different port than the static
        // frontend. Never replace this with a token stored in JS.
        credentials: "include",
        headers: {
          ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
          ...(headers || {})
        },
        body: body !== undefined ? JSON.stringify(body) : undefined
      });
    } catch (networkError) {
      throw new ApiError(
        "Could not reach the PawAI server. Check your connection and try again.",
        { status: 0 }
      );
    }

    let data = null;
    const text = await response.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (parseError) {
        data = null;
      }
    }

    if (!response.ok) {
      const parsed = parseDetail(data && data.detail);
      throw new ApiError(
        (parsed && parsed.message) || statusFallbackMessage(response.status),
        {
          status: response.status,
          fieldErrors: (parsed && parsed.fieldErrors) || [],
          raw: data
        }
      );
    }

    return data;
  }

  const PawAIApi = {
    ApiError,

    /**
     * POST /api/auth/register
     * payload: { email, username, password, pet?: { name, breed?, age?, gender? } }
     * Auto-logs in on success (backend sets the session cookie).
     * Returns { user, pet }.
     */
    register(payload) {
      return request("/api/auth/register", { method: "POST", body: payload });
    },

    /**
     * POST /api/auth/login
     * identifier: username OR email.
     * Returns the UserOut object on success.
     */
    login(identifier, password) {
      return request("/api/auth/login", { method: "POST", body: { identifier, password } });
    },

    /** POST /api/auth/logout - clears the server-side session + cookie. */
    logout() {
      return request("/api/auth/logout", { method: "POST" });
    },

    /** GET /api/auth/me - throws ApiError(status 401) if not authenticated. */
    me() {
      return request("/api/auth/me", { method: "GET" });
    },

    /** GET /api/pets - pets belonging to the authenticated user. */
    listPets() {
      return request("/api/pets", { method: "GET" });
    },

    /** POST /api/pets */
    createPet(payload) {
      return request("/api/pets", { method: "POST", body: payload });
    },
    
    /** PATCH /api/pets/{petId} */
    updatePet(petId, payload) {
      return request(`/api/pets/${encodeURIComponent(petId)}`, {
        method: "PATCH",
        body: payload
      });
    },
    
    /** POST /api/contact - sends an owner-facing contact message. */
    sendContact(payload) {
      return request("/api/contact", { method: "POST", body: payload });
    },
    listMedia(animalType) {
      return request(`/api/media${animalType ? `?animal_type=${encodeURIComponent(animalType)}` : ""}`);
    },
    uploadMedia(file, animalType, petId) {
  const form = new FormData();
  form.append("file", file);
  form.append("animal_type", animalType);

  if (petId) {
    form.append("pet_id", petId);
  }

  return fetch(`${API_BASE_URL}/api/media`, {
    method: "POST",
    credentials: "include",
    body: form
  }).then(async (response) => {
    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        data.detail || statusFallbackMessage(response.status),
        {
          status: response.status,
          raw: data
        }
      );
    }

    return data;
  });
},

analyzeMedia(mediaId) {
  return request(`/api/analyze/${encodeURIComponent(mediaId)}`, {
    method: "POST"
  });
}
  };

  /**
   * Guard for pages that require a logged-in user. Call at the top of the
   * page's script:
   *
   *   const user = await PawAIAuth.requireUser();
   *   if (!user) return; // already redirecting to login
   *
   * Redirects to 02-login.html on a 401. Network failures are rethrown after
   * the page is made visible, allowing the caller to present a safe fallback.
   */
  async function requireUser({ loginPage = "02-login.html" } = {}) {
    try {
      const user = await PawAIApi.me();
      // Protected pages begin hidden, preventing a flash of private content
      // before the server-side session is checked.
      document.documentElement.classList.remove("auth-pending");
      return user;
    } catch (error) {
      // A server/network outage must never leave the document permanently
      // invisible. Pages can render their safe default UI while their own
      // caller decides how to present the network error.
      document.documentElement.classList.remove("auth-pending");
      if (error instanceof ApiError && error.isUnauthorized) {
        global.location.href = loginPage;
        return null;
      }
      throw error;
    }
  }

  /**
   * Wires up a logout control (button or link) to POST /api/auth/logout and
   * then redirect to the login page, regardless of whether the backend call
   * succeeds (a session that's already gone server-side should still send
   * the user back to the login screen).
   */
  function bindLogout(selectorOrElement, { loginPage = "02-login.html" } = {}) {
    const element =
      typeof selectorOrElement === "string"
        ? document.querySelector(selectorOrElement)
        : selectorOrElement;
    if (!element) return;

    element.addEventListener("click", async (event) => {
      event.preventDefault();
      try {
        await PawAIApi.logout();
      } catch (error) {
        // Even if the network call fails, don't trap the user on the page -
        // fall through to the redirect below.
      } finally {
        global.location.href = loginPage;
      }
    });
  }

  global.PawAIApi = PawAIApi;
  global.PawAIAuth = { requireUser, bindLogout };
})(window);
