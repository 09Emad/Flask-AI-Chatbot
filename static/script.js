const messagesContainer = document.getElementById('messages-container');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const clearButton = document.getElementById('clear-chat');
const sessionBadge = document.getElementById('session-badge');
const templateBar = document.getElementById('template-bar');
const modelPicker = document.getElementById('model-picker');
const currentModelLabel = document.getElementById('current-model-label');
const metricsStatus = document.getElementById('metrics-status');
const sourcesList = document.getElementById('sources-list');

const STORAGE_KEY = 'llm_rag_assistant_messages';
const SESSION_KEY = 'llm_rag_assistant_session_id';
const MODEL_KEY = 'llm_rag_assistant_model_name';

let currentSessionId = localStorage.getItem(SESSION_KEY) || '';
let currentModelName = localStorage.getItem(MODEL_KEY) || '';

const loadMessages = () => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
};

const saveMessages = (messages) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
};

const saveSessionId = (sessionId) => {
  currentSessionId = sessionId;
  localStorage.setItem(SESSION_KEY, sessionId);
};

const saveModelName = (modelName) => {
  currentModelName = modelName;
  localStorage.setItem(MODEL_KEY, modelName);
  if (currentModelLabel) {
    currentModelLabel.textContent = modelName;
  }
};

const renderStoredMessages = () => {
  const messages = loadMessages();
  messagesContainer.innerHTML = '';
  messages.forEach(({ message, role, imgSrc }) => addMessage(message, role, imgSrc, false));
};

const persistMessage = (message, role, imgSrc) => {
  const messages = loadMessages();
  messages.push({ message, role, imgSrc });
  saveMessages(messages);
};

const addMessage = (message, role, imgSrc, persist = true) => {
  const messageElement = document.createElement('div');
  const textElement = document.createElement('p');
  const imgElement = document.createElement('img');
  const clearDiv = document.createElement('div');

  messageElement.className = `message ${role}`;
  imgElement.src = imgSrc;
  textElement.innerText = message;

  messageElement.appendChild(imgElement);
  messageElement.appendChild(textElement);
  messagesContainer.appendChild(messageElement);

  clearDiv.className = 'clear';
  messagesContainer.appendChild(clearDiv);

  if (persist) {
    persistMessage(message, role, imgSrc);
  }
};

const setLoadingState = (isLoading) => {
  const existingAnimation = document.querySelector('.loading-animation');
  const existingText = document.querySelector('.loading-text');

  if (!isLoading) {
    if (existingAnimation) existingAnimation.remove();
    if (existingText) existingText.remove();
    return;
  }

  const loadingElement = document.createElement('div');
  const loadingTextElement = document.createElement('p');
  loadingElement.className = 'loading-animation';
  loadingTextElement.className = 'loading-text';
  loadingTextElement.innerText = 'Retrieving sources and generating an answer...';
  messagesContainer.appendChild(loadingElement);
  messagesContainer.appendChild(loadingTextElement);
};

const updateMetrics = (sessionSummary = {}) => {
  metricsStatus.textContent = sessionSummary.message_count ? 'active' : 'ready';
  if (sessionSummary.id) {
    sessionBadge.textContent = sessionSummary.id.slice(0, 8);
  }
};

const renderSources = (sources = []) => {
  sourcesList.innerHTML = '';

  if (!sources.length) {
    const empty = document.createElement('p');
    empty.className = 'muted-note';
    empty.textContent = 'No sources retrieved yet.';
    sourcesList.appendChild(empty);
    return;
  }

  sources.forEach((source) => {
    const item = document.createElement('div');
    item.className = 'source-item';
    item.innerHTML = `
      <strong>${source.title}</strong>
      <span>${source.source}</span>
      <small>score ${source.score}</small>
    `;
    sourcesList.appendChild(item);
  });
};

const renderModelPicker = async () => {
  const response = await fetch('/models');
  const payload = await response.json();
  modelPicker.innerHTML = '';

  payload.models.forEach((model) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'model-chip';
    button.innerHTML = `
      <span>${model.family}</span>
      <strong>${model.name}</strong>
      <small>${model.description}</small>
    `;

    if (currentModelName === model.name || (!currentModelName && model.is_default)) {
      button.classList.add('selected');
      saveModelName(model.name);
    }

    button.addEventListener('click', () => {
      document.querySelectorAll('.model-chip').forEach((chip) => chip.classList.remove('selected'));
      button.classList.add('selected');
      saveModelName(model.name);
      addMessage(`Switched to model: ${model.name}`, 'aibot', '../static/Bot_logo.png');
    });

    modelPicker.appendChild(button);
  });
};

const ensureSession = async () => {
  const response = await fetch('/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSessionId || null }),
  });

  const payload = await response.json();
  if (payload?.session?.id) {
    saveSessionId(payload.session.id);
    updateMetrics(payload.session);
  }
};

const makePostRequest = async (message) => {
  const response = await fetch('/chatbot', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: message,
      session_id: currentSessionId || null,
      model_name: currentModelName || null,
    }),
  });

  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || 'Request failed');
  }

  if (payload?.session?.id) {
    saveSessionId(payload.session.id);
    updateMetrics(payload.session);
  }

  renderSources(payload.sources || []);
  return payload;
};

const sendMessage = async (message) => {
  addMessage(message, 'user', '../static/user.jpeg');
  setLoadingState(true);

  try {
    const data = await makePostRequest(message);
    addMessage(data.response, 'aibot', '../static/Bot_logo.png');
    updateMetrics(data.session);
  } catch (error) {
    addMessage(error.message, 'error', '../static/Error.png');
  } finally {
    setLoadingState(false);
  }
};

const loadPromptTemplates = async () => {
  const response = await fetch('/templates');
  const payload = await response.json();
  templateBar.innerHTML = '';

  payload.templates.forEach((template) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = template.label;
    button.addEventListener('click', () => {
      messageInput.value = template.prompt;
      messageInput.focus();
    });
    templateBar.appendChild(button);
  });
};

messageForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();

  if (!message) {
    return;
  }

  messageInput.value = '';
  await sendMessage(message);
});

clearButton.addEventListener('click', async () => {
  localStorage.removeItem(STORAGE_KEY);
  messagesContainer.innerHTML = '';
  renderSources([]);

  try {
    const response = await fetch('/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentSessionId || null }),
    });
    const payload = await response.json();
    if (payload?.session?.id) {
      saveSessionId(payload.session.id);
      updateMetrics(payload.session);
    }
  } catch {
    // Best-effort reset only.
  }
});

(async () => {
  renderStoredMessages();
  renderSources([]);
  await ensureSession();
  await loadPromptTemplates();
  await renderModelPicker();
})();
