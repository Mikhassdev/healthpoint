// app.js — Validación reactiva (con "touched" para no mostrar errores al inicio)
console.log('HealthPoint JS activo');

document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('.forms-container .form-card form');

  const re = {
    letters: /^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$/,
    alnum:   /^[A-Za-z0-9ÁÉÍÓÚÑáéíóúñ\s]+$/,
    // Nombres reales: "Jeringa 5 ml", "Mascarilla N95", "Box 2-A", "Dra. Pérez"
    texto:   /^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ\s.,\-\/()%°#]+$/,
    number:  /^\d+$/
  };

  const msg = {
    required: 'Este campo es obligatorio.',
    letters:  'Solo letras (incluye tildes y espacios).',
    alnum:    'Solo letras y números (incluye espacios).',
    texto:    'Usa letras, números, espacios y . , - / ( ) % ° #',
    number:   'Solo números enteros positivos.',
    gt0:      'Debe ser un entero mayor a 0.',
    ge0:      'Debe ser un entero mayor o igual a 0.'
  };

  function ensureErrorBelow(input) {
    let holder = input.parentElement.querySelector('.hp-error');
    if (!holder) {
      holder = document.createElement('div');
      holder.className = 'hp-error';
      input.parentElement.appendChild(holder);
    }
    return holder;
  }
  function setError(input, text) {
    const holder = ensureErrorBelow(input);
    holder.textContent = text || '';
    input.classList.toggle('invalid', Boolean(text));
  }
  function clearError(input) { setError(input, ''); }

  /**
   * Valida un input según "rule".
   * - display=false: evalúa pero NO muestra mensajes (para estado inicial / cálculo de botón)
   * - display=true: muestra/borra mensajes según corresponda
   */
  function validateInput(input, rule, opts = {}, display = true) {
    const raw = (input.value || '').trim();

    // requerido
    if (opts.required && raw.length === 0) {
      if (display) setError(input, msg.required);
      return false;
    }
    // vacío no requerido
    if (!raw.length) {
      if (display) clearError(input);
      return true;
    }

    // chequeo por regla
    if (rule === 'letters' && !re.letters.test(raw)) {
      if (display) setError(input, msg.letters);
      return false;
    }
    if (rule === 'alnum' && !re.alnum.test(raw)) {
      if (display) setError(input, msg.alnum);
      return false;
    }
    if (rule === 'texto' && !re.texto.test(raw)) {
      if (display) setError(input, msg.texto);
      return false;
    }
    if (rule === 'number') {
      if (!re.number.test(raw)) {
        if (display) setError(input, msg.number);
        return false;
      }
      const n = Number(raw);
      if (opts.gt0 && !(Number.isInteger(n) && n > 0)) {
        if (display) setError(input, msg.gt0);
        return false;
      }
      if (opts.ge0 && !(Number.isInteger(n) && n >= 0)) {
        if (display) setError(input, msg.ge0);
        return false;
      }
    }

    if (display) clearError(input);
    return true;
  }

  function kindFromActionOrFields(form) {
    const action = (form.getAttribute('action') || '').toLowerCase();
    if (action.includes('/insert/insumo'))      return 'insumo';
    if (action.includes('/insert/box'))         return 'box';
    if (action.includes('/insert/movimiento'))  return 'mov';

    // Fallback por campos
    const hasUnidad   = !!form.querySelector('[name="unidad"]');
    const hasStock    = !!form.querySelector('[name="stock"]');
    const hasResp     = !!form.querySelector('[name="responsable"]');
    const hasTipo     = !!form.querySelector('[name="tipo"]');
    const hasCant     = !!form.querySelector('[name="cantidad"]');

    if (hasUnidad && hasStock) return 'insumo';
    if (hasResp && !hasUnidad) return 'box';
    if (hasTipo && hasCant)    return 'mov';
    return 'desconocido';
  }

  // Lista desplegable obligatoria: basta con que haya una opción elegida.
  function validateSelect(el, display) {
    const ok = !!el.value;
    if (display) { ok ? clearError(el) : setError(el, msg.required); }
    return ok;
  }

  forms.forEach(form => {
    const kind = kindFromActionOrFields(form);
    const submitBtn = form.querySelector('button[type="submit"]');

    const rules = {
      insumo: {
        nombre:   (el, disp)=>validateInput(el,'texto',{required:true}, disp),
        unidad:   (el, disp)=>validateInput(el,'texto',{required:true}, disp),
        stock:    (el, disp)=>validateInput(el,'number',{required:true, ge0:true}, disp),
      },
      box: {
        nombre:       (el, disp)=>validateInput(el,'texto',{required:true}, disp),
        responsable:  (el, disp)=>validateInput(el,'texto',{required:true}, disp),
      },
      mov: {
        tipo:     validateSelect,
        insumo:   validateSelect,
        cantidad: (el, disp)=>validateInput(el,'number',{required:true, gt0:true}, disp),
        box:      validateSelect,
      }
    }[kind] || {};

    // --- Estado "tocado" por campo: no mostrar errores hasta que interactúe ---
    const touched = new WeakSet();

    function validateAll(display = false) {
      let ok = true;
      Object.keys(rules).forEach(name => {
        const el = form.querySelector(`[name="${name}"]`);
        if (!el) return;
        const show = display || touched.has(el); // muestra si submit o campo ya tocado
        ok = rules[name](el, show) && ok;
      });
      if (submitBtn) submitBtn.disabled = !ok;
      return ok;
    }

    // Eventos por campo: marcan como "tocado" y muestran errores si aplica
    Object.keys(rules).forEach(name => {
      const el = form.querySelector(`[name="${name}"]`);
      if (!el) return;

      const evt = (el.tagName === 'SELECT') ? 'change' : 'input';
      el.addEventListener(evt, () => {
        touched.add(el);
        validateAll(false);          // recalcula botón sin mostrar otros errores
        rules[name](el, true);       // muestra solo el del campo que cambió
      });
      el.addEventListener('blur', () => {
        touched.add(el);
        rules[name](el, true);
        validateAll(false);
      });
    });

    // Estado inicial: botón coherente, sin mensajes visibles
    validateAll(false);

    // Submit: marca todo como "tocado" y muestra errores si existen
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      // forzar "touched" de todos los campos con regla
      Object.keys(rules).forEach(name => {
        const el = form.querySelector(`[name="${name}"]`);
        if (el) touched.add(el);
      });
      if (!validateAll(true)) return;   // muestra y detiene si hay errores
      form.submit();
    });
  });
});

// --- Toasts (mensajes Django) ---
document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('toast-root');
  if (!root) return;

  const toasts = Array.from(root.querySelectorAll('.hp-toast'));

  toasts.forEach((el, i) => {
    // auto-cierre escalonado
    const ttl = 3800 + i * 300;   // ms
    const timer = setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      setTimeout(() => el.remove(), 250);
    }, ttl);

    // cerrar al click
    el.addEventListener('click', () => {
      clearTimeout(timer);
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      setTimeout(() => el.remove(), 250);
    });
  });
});


// VALIDACIÓN LOGIN HEALTHPOINT
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  if (!loginForm) return; // no estamos en la página de login

  const usernameInput = loginForm.querySelector('#id_username');
  const passwordInput = loginForm.querySelector('#id_password');
  const userError     = loginForm.querySelector('[data-error-for="username"]');
  const passError     = loginForm.querySelector('[data-error-for="password"]');

  function showError(elError, message) {
    if (!elError) return;
    elError.textContent = message || '';
  }

  // En el login solo se exige que los campos no estén vacíos. Las reglas de
  // formato (usuario, complejidad de la clave) se aplican al CREAR la cuenta;
  // aplicarlas aquí bloqueaba a usuarios válidos, como "bodega_1" o un
  // superusuario creado con createsuperuser.
  function validateRequired(input, elError, label) {
    if (!input) return true;
    const ok = (input.value || '').length > 0;
    showError(elError, ok ? '' : `El campo ${label} es obligatorio.`);
    input.classList.toggle('input-error', !ok);
    return ok;
  }

  const validateUsername = () => validateRequired(usernameInput, userError, 'Usuario');
  const validatePassword = () => validateRequired(passwordInput, passError, 'Contraseña');

  // Validación en tiempo real
  if (usernameInput) {
    usernameInput.addEventListener('input', validateUsername);
    usernameInput.addEventListener('blur', validateUsername);
  }

  if (passwordInput) {
    passwordInput.addEventListener('input', validatePassword);
    passwordInput.addEventListener('blur', validatePassword);
  }

  // Validación al enviar
  loginForm.addEventListener('submit', (e) => {
    const okUser = validateUsername();
    const okPass = validatePassword();

    if (!okUser || !okPass) {
      e.preventDefault();
    }
  });
});

// ======================================================
//  Validación reactiva para registrar_usuario.html
// ======================================================
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('register-form');
  if (!form) return; // si no estamos en la página de registro, no hace nada

  const username   = form.querySelector('#id_username');
  const firstName  = form.querySelector('#id_first_name');
  const lastName   = form.querySelector('#id_last_name');
  const email      = form.querySelector('#id_email');
  const role       = form.querySelector('#id_role');
  const pass1      = form.querySelector('#id_password1');
  const pass2      = form.querySelector('#id_password2');

  function getErrorEl(input) {
    const label = input.closest('label');
    return label ? label.querySelector('.field-error') : null;
  }

  function showFieldError(input, message) {
    const err = getErrorEl(input);
    if (err) err.textContent = message || '';
    if (message) {
      input.classList.add('input-error');
    } else {
      input.classList.remove('input-error');
    }
  }

  // --- Reglas individuales ---

  // Solo letras (usuario, nombres, apellidos)
  const reLetters = /^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$/;

  // Email simple
  const reEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function validateUsername() {
    const value = (username.value || '').trim();
    if (!value) {
      showFieldError(username, 'El nombre de usuario es obligatorio.');
      return false;
    }
    if (!/^[A-Za-zÁÉÍÓÚÑáéíóúñ]+$/.test(value)) {
      showFieldError(username, 'Solo se permiten letras mayúsculas y minúsculas (sin números ni símbolos).');
      return false;
    }
    showFieldError(username, '');
    return true;
  }

  function validateFirstName() {
    const value = (firstName.value || '').trim();
    if (!value) {
      showFieldError(firstName, 'El nombre es obligatorio.');
      return false;
    }
    if (!reLetters.test(value)) {
      showFieldError(firstName, 'Solo letras (puede incluir tildes y espacios).');
      return false;
    }
    showFieldError(firstName, '');
    return true;
  }

  function validateLastName() {
    const value = (lastName.value || '').trim();
    if (!value) {
      showFieldError(lastName, 'Los apellidos son obligatorios.');
      return false;
    }
    if (!reLetters.test(value)) {
      showFieldError(lastName, 'Solo letras (puede incluir tildes y espacios).');
      return false;
    }
    showFieldError(lastName, '');
    return true;
  }

  function validateEmail() {
    const value = (email.value || '').trim();
    if (!value) {
      showFieldError(email, 'El correo electrónico es obligatorio.');
      return false;
    }
    if (!reEmail.test(value)) {
      showFieldError(email, 'Ingresa un correo electrónico válido.');
      return false;
    }
    showFieldError(email, '');
    return true;
  }

  function validateRole() {
    const value = role.value;
    if (!value) {
      showFieldError(role, 'Debes seleccionar un rol para el usuario.');
      return false;
    }
    showFieldError(role, '');
    return true;
  }

  function validatePassword1() {
    const value = pass1.value || '';

    if (!value) {
      showFieldError(pass1, 'La contraseña es obligatoria.');
      return false;
    }
    if (value.length < 5) {
      showFieldError(pass1, 'Debe tener al menos 5 caracteres.');
      return false;
    }
    if (!/[A-Z]/.test(value)) {
      showFieldError(pass1, 'Debe contener al menos una letra mayúscula.');
      return false;
    }
    if (!/[0-9]/.test(value)) {
      showFieldError(pass1, 'Debe contener al menos un número.');
      return false;
    }
    if (!/[^\w\s]/.test(value)) {
      showFieldError(pass1, 'Debe incluir al menos un carácter especial.');
      return false;
    }

    showFieldError(pass1, '');
    return true;
  }

  function validatePassword2() {
    const value1 = pass1.value || '';
    const value2 = pass2.value || '';

    if (!value2) {
      showFieldError(pass2, 'Debes repetir la contraseña.');
      return false;
    }
    if (value1 !== value2) {
      showFieldError(pass2, 'Las contraseñas no coinciden.');
      return false;
    }

    showFieldError(pass2, '');
    return true;
  }

  // --- Validación en tiempo real ---

  if (username)   username.addEventListener('input', validateUsername);
  if (firstName)  firstName.addEventListener('input', validateFirstName);
  if (lastName)   lastName.addEventListener('input', validateLastName);
  if (email)      email.addEventListener('input', validateEmail);
  if (role)       role.addEventListener('change', validateRole);
  if (pass1)      pass1.addEventListener('input', validatePassword1);
  if (pass2)      pass2.addEventListener('input', validatePassword2);

  // --- Validación al enviar el formulario ---
  form.addEventListener('submit', (e) => {
    const okUser  = validateUsername();
    const okName  = validateFirstName();
    const okLast  = validateLastName();
    const okEmail = validateEmail();
    const okRole  = validateRole();
    const okP1    = validatePassword1();
    const okP2    = validatePassword2();

    if (!okUser || !okName || !okLast || !okEmail || !okRole || !okP1 || !okP2) {
      e.preventDefault(); // bloquea el envío si algo falla
    }
  });
});


// --- Confirmación antes de acciones destructivas ---
// Cualquier formulario con data-confirm pide confirmación antes de enviarse.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
});
