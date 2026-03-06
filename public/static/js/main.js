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
const saveBtn = document.getElementById('save-btn');
const outputEl = document.getElementById('output');
const configBtn = document.getElementById('config-btn');
const modal = document.getElementById('config-modal');
const closeBtn = document.getElementsByClassName('close')[0];
const grammarInput = document.getElementById('grammar-input');
const errorList = document.getElementById('error-list');
const saveConfigBtn = document.getElementById('save-config');

saveBtn.addEventListener('click', () => {
    const code = editor.getValue();
    const blob = new Blob([code], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'program.ppy';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
});

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
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = data.error;
            outputEl.appendChild(errorDiv);
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
