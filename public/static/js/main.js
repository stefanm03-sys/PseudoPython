require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});

let editor;

require(['vs/editor/editor.main'], function() {
    editor = monaco.editor.create(document.getElementById('editor-container'), {
        value: 'var x is 10\nstate(x)\n',
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true
    });
});

const runBtn = document.getElementById('run-btn');
const outputEl = document.getElementById('output');
const configBtn = document.getElementById('config-btn');
const modal = document.getElementById('config-modal');
const closeBtn = document.getElementsByClassName('close')[0];
const grammarInput = document.getElementById('grammar-input');
const errorList = document.getElementById('error-list');
const saveConfigBtn = document.getElementById('save-config');

runBtn.addEventListener('click', async () => {
    const code = editor.getValue();
    outputEl.textContent = 'Running...';
    
    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        const data = await response.json();
        
        outputEl.textContent = data.output;
        if (data.error) {
            outputEl.innerHTML += `<div class="error">\n${data.error}</div>`;
        }
    } catch (err) {
        outputEl.textContent = 'Error connecting to server: ' + err.message;
    }
});

configBtn.addEventListener('click', async () => {
    const response = await fetch('/api/config');
    const config = await response.json();
    
    grammarInput.value = config.grammar;
    
    errorList.innerHTML = '';
    for (const [code, template] of Object.entries(config.errors)) {
        const label = document.createElement('label');
        label.textContent = code;
        const input = document.createElement('input');
        input.value = template;
        input.dataset.code = code;
        errorList.appendChild(label);
        errorList.appendChild(input);
    }
    
    modal.style.display = 'block';
});

closeBtn.onclick = () => modal.style.display = 'none';
window.onclick = (event) => { if (event.target == modal) modal.style.display = 'none'; };

saveConfigBtn.addEventListener('click', async () => {
    const grammar = grammarInput.value;
    const errors = {};
    errorList.querySelectorAll('input').forEach(input => {
        errors[input.dataset.code] = input.value;
    });
    
    const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grammar, errors })
    });
    const result = await response.json();
    alert(result.message);
    modal.style.display = 'none';
});
