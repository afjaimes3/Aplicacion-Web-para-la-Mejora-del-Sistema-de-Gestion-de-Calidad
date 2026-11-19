document.addEventListener('DOMContentLoaded', function () {
    // --- LÓGICA DE SELECTORES EN CASCADA (PROCESO -> SUBPROCESO) ---

    const selectProceso = document.getElementById('pro');
    const selectSubproceso = document.getElementById('sp');
    const selectTipoDoc = document.getElementById('tipod');

    function actualizarSubprocesos() {
        const procesoSeleccionado = selectProceso.value;

        // Limpiar opciones anteriores
        selectSubproceso.innerHTML = '<option value="">-- Seleccione Subproceso --</option>';

        if (procesoSeleccionado && SUBPROCESOS_DATA[procesoSeleccionado]) {
            const opciones = SUBPROCESOS_DATA[procesoSeleccionado];

            opciones.forEach(sub => {
                const option = document.createElement('option');
                option.value = sub.codigo;
                option.textContent = `${sub.codigo} - ${sub.nombre}`;
                selectSubproceso.appendChild(option);
            });

            // Si estamos editando y había un valor previo, seleccionarlo
            if (typeof VALOR_SUBPROCESO_PREVIO !== 'undefined' && VALOR_SUBPROCESO_PREVIO) {
                // Verificar si el valor previo pertenece al grupo actual para evitar errores lógicos
                const existe = opciones.some(o => o.codigo === VALOR_SUBPROCESO_PREVIO);
                if (existe) {
                    selectSubproceso.value = VALOR_SUBPROCESO_PREVIO;
                }
            }
        }
    }

    function actualizarSecciones() {
        const tipoSeleccionado = selectTipoDoc.value;
        const allSections = ['section-1', 'section-2', 'section-3', 'section-4', 'section-5', 'section-6', 'section-7', 'section-8', 'section-9', 'section-11'];

        // Ocultar todas inicialmente
        allSections.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });

        if (tipoSeleccionado === 'DI' || tipoSeleccionado === 'PR') {
            // Mostrar todas
            allSections.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = 'block';
            });
        } else if (tipoSeleccionado === 'FR' || tipoSeleccionado === 'IN') {
            // Mostrar solo sección 11 (Aprobación)
            const el11 = document.getElementById('section-11');
            if (el11) el11.style.display = 'block';
        }
    }

    // Escuchar cambios en el proceso
    if (selectProceso) {
        selectProceso.addEventListener('change', actualizarSubprocesos);

        // Ejecutar al inicio por si venimos de "Editar" y ya hay un proceso seleccionado
        if (selectProceso.value) {
            actualizarSubprocesos();
        }
    }

    // Escuchar cambios en el tipo de documento
    if (selectTipoDoc) {
        selectTipoDoc.addEventListener('change', actualizarSecciones);

        // Ejecutar al inicio
        if (selectTipoDoc.value) {
            actualizarSecciones();
        }
    }


    // --- LÓGICA RECONOCIMIENTO DE VOZ (Igual que antes) ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    // --- CHECK GLOBAL IA ---
    if (typeof ENABLE_IA_GLOBAL !== 'undefined' && !ENABLE_IA_GLOBAL) {
        document.querySelectorAll('.btn-ai').forEach(btn => btn.style.display = 'none');
    }

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.interimResults = false;

        document.querySelectorAll('.mic-btn').forEach(button => {
            button.addEventListener('click', () => {
                const targetId = button.dataset.target;
                const targetTextarea = document.getElementById(targetId);

                recognition.start();
                button.classList.add('recording');
                button.textContent = '...';

                recognition.onresult = (event) => {
                    const speechResult = event.results[0][0].transcript;
                    // Agregar espacio si ya hay texto
                    if (targetTextarea.value.length > 0) {
                        targetTextarea.value += " " + speechResult;
                    } else {
                        targetTextarea.value = speechResult;
                    }
                };

                recognition.onspeechend = () => {
                    recognition.stop();
                    button.classList.remove('recording');
                    button.textContent = '🎤';
                };

                recognition.onerror = () => {
                    button.classList.remove('recording');
                    button.textContent = '🎤';
                };
            });
        });
    } else {
        document.querySelectorAll('.mic-btn').forEach(btn => btn.style.display = 'none');
    }

    // --- TABLAS DINÁMICAS (Igual que antes) ---
    // --- TABLAS DINÁMICAS (Con auto-numeración) ---

    function recalcNumeros(tableId, inputName) {
        const tableBody = document.querySelector(`#${tableId} tbody`);
        const rows = tableBody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            const input = row.querySelector(`input[name="${inputName}"]`);
            if (input) {
                input.value = index + 1;
            }
        });
    }

    // Variables UI IA
    const iaModal = document.getElementById('iaModal');
    const iaSuggestionText = document.getElementById('ia-suggestion-text');
    const iaTargetIdInput = document.getElementById('ia-target-id');
    const btnIaReject = document.getElementById('btn-ia-reject');
    const btnIaAccept = document.getElementById('btn-ia-accept');
    const closeModal = document.querySelector('.close');
    let iaIsTable = false;

    // --- TABLAS DINÁMICAS (Core) ---

    function addTableRow(tableId, htmlRow, numInputName) {
        const tbody = document.querySelector('#' + tableId + ' tbody');
        const newRow = document.createElement('tr');
        newRow.innerHTML = htmlRow;
        tbody.appendChild(newRow);

        if (numInputName) {
            recalcNumeros(tableId, numInputName);
        }
    }

    // Event Listeners: Agregar filas manualmente
    const btnAddActividad = document.getElementById('btn-add-actividad');
    if (btnAddActividad) {
        btnAddActividad.addEventListener('click', () => {
            const html = `
                <td><input type="text" name="actividad_no" readonly style="background-color: #eee;"></td>
                <td><textarea name="actividad_responsable"></textarea></td>
                <td><textarea name="actividad_descripcion"></textarea></td>
                <td><textarea name="actividad_registro"></textarea></td>
                <td><button type="button" class="btn-remove">X</button></td>
             `;
            addTableRow('tabla-actividades', html, 'actividad_no');
        });
    }

    const btnAddDocumento = document.getElementById('btn-add-documento');
    if (btnAddDocumento) {
        btnAddDocumento.addEventListener('click', () => {
            const html = `
                <td><input type="text" name="doc_institucional"></td>
                <td><input type="text" name="doc_nombre"></td>
                <td><input type="text" name="doc_codigo"></td>
                <td><button type="button" class="btn-remove">X</button></td>
             `;
            addTableRow('tabla-documentos', html, null);
        });
    }

    const btnAddAnexo = document.getElementById('btn-add-anexo');
    if (btnAddAnexo) {
        btnAddAnexo.addEventListener('click', () => {
            const html = `
                <td><input type="text" name="anexo_no" readonly style="background-color: #eee;"></td>
                <td><input type="text" name="anexo_nombre"></td>
                <td><input type="text" name="anexo_descripcion"></td>
                <td><button type="button" class="btn-remove">X</button></td>
             `;
            addTableRow('tabla-anexos', html, 'anexo_no');
        });
    }

    // Event delegation para botones eliminar (X)
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('btn-remove')) {
            const row = e.target.closest('tr');
            const table = row.closest('table');
            const tableId = table.id;

            row.remove();

            if (tableId === 'tabla-actividades') recalcNumeros('tabla-actividades', 'actividad_no');
            if (tableId === 'tabla-anexos') recalcNumeros('tabla-anexos', 'anexo_no');
        }
    });

    let iaOriginalData = null; // Para control de errores si es tabla

    // Cerrar modal
    function closeModalFunc() {
        iaModal.style.display = 'none';
        iaSuggestionText.value = '';
        if (iaSuggestionTableContainer) {
            iaSuggestionTableContainer.style.display = 'none';
            iaSuggestionTableContainer.innerHTML = '';
        }
        const iaAnalysis = document.getElementById('ia-suggestion-analysis');
        if (iaAnalysis) {
            iaAnalysis.style.display = 'none';
            document.getElementById('ia-analysis-content').textContent = '';
        }
    }

    if (btnIaReject) btnIaReject.addEventListener('click', closeModalFunc);
    if (closeModal) closeModal.addEventListener('click', closeModalFunc);
    // El usuario pidió que NO se cierre al hacer clic fuera.
    /*
    window.onclick = function (event) {
        if (event.target == iaModal) {
            closeModalFunc();
        }
    }
    */

    // Helper: Leer datos de tabla
    function getTableData(tableId) {
        const rows = document.querySelectorAll('#' + tableId + ' tbody tr');
        const data = [];

        rows.forEach(row => {
            const inputs = row.querySelectorAll('input, textarea');
            const rowData = {};
            inputs.forEach(input => {
                if (input.name && input.type !== 'hidden') {
                    // Mapeo simple nombre -> valor
                    rowData[input.name] = input.value;
                }
            });
            // Solo agregar si tiene algo de contenido
            if (Object.values(rowData).some(val => val.trim() !== '')) {
                data.push(rowData);
            }
        });
        return data;
    }

    // Helper: Leer datos de contexto
    function getContextData() {
        return {
            tipod: document.getElementById('tipod').value || '',
            pro: document.getElementById('pro').value || '',
            sp: document.getElementById('sp').value || '',
            titulodocumento: document.getElementById('titulodocumento').value || '',
            objetivo: document.getElementById('objetivo') ? document.getElementById('objetivo').value : '',
            alcance: document.getElementById('alcance') ? document.getElementById('alcance').value : ''
        };
    }

    const iaSuggestionTableContainer = document.getElementById('ia-suggestion-table-container');

    // Helper: Renderizar tabla en modal
    function renderModalTable(data, targetId) {
        iaSuggestionTableContainer.innerHTML = '';
        const table = document.createElement('table');
        table.className = 'w-full border-collapse';
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';

        // Headers
        let headers = [];
        if (targetId === 'tabla-actividades') {
            headers = ['No.', 'Responsable', 'Actividad', 'Registro'];
        } else if (targetId === 'tabla-documentos') {
            headers = ['Tipo Inst.', 'Nombre', 'Código'];
        } else if (targetId === 'tabla-anexos') {
            headers = ['No.', 'Nombre', 'Descripción'];
        }

        const thead = document.createElement('thead');
        const trHead = document.createElement('tr');
        headers.forEach(h => {
            const th = document.createElement('th');
            th.textContent = h;
            th.style.backgroundColor = '#f2f2f2';
            th.style.padding = '8px';
            th.style.border = '1px solid #ddd';
            th.style.textAlign = 'left';
            trHead.appendChild(th);
        });
        thead.appendChild(trHead);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        data.forEach(row => {
            const tr = document.createElement('tr');

            if (targetId === 'tabla-actividades') {
                tr.innerHTML = `
                    <td style="padding: 5px; border: 1px solid #ddd;"><input type="text" class="full-width" data-key="actividad_no" value="${row.actividad_no || ''}" readonly style="background-color: #eee; width: 100%;"></td>
                    <td style="padding: 5px; border: 1px solid #ddd;"><textarea class="full-width" data-key="actividad_responsable" style="width: 100%;">${row.actividad_responsable || ''}</textarea></td>
                    <td style="padding: 5px; border: 1px solid #ddd;"><textarea class="full-width" data-key="actividad_descripcion" style="width: 100%;">${row.actividad_descripcion || ''}</textarea></td>
                    <td style="padding: 5px; border: 1px solid #ddd;"><textarea class="full-width" data-key="actividad_registro" style="width: 100%;">${row.actividad_registro || ''}</textarea></td>
                 `;
            } else if (targetId === 'tabla-documentos') {
                tr.innerHTML = `
                    <td style="padding: 5px; border: 1px solid #ddd;"><input type="text" class="full-width" data-key="doc_institucional" value="${row.doc_institucional || ''}" style="width: 100%;"></td>
                    <td style="padding: 5px; border: 1px solid #ddd;"><input type="text" class="full-width" data-key="doc_nombre" value="${row.doc_nombre || ''}" style="width: 100%;"></td>
                    <td style="padding: 5px; border: 1px solid #ddd;"><input type="text" class="full-width" data-key="doc_codigo" value="${row.doc_codigo || ''}" style="width: 100%;"></td>
                 `;
            } else if (targetId === 'tabla-anexos') {
                tr.innerHTML = `
                    <td style="padding: 5px; border: 1px solid #ddd;"><input type="text" class="full-width" data-key="anexo_no" value="${row.anexo_no || ''}" readonly style="background-color: #eee; width: 100%;"></td>
                    <td style="padding: 5px; border: 1px solid #ddd;"><input type="text" class="full-width" data-key="anexo_nombre" value="${row.anexo_nombre || ''}" style="width: 100%;"></td>
                    <td style="padding: 5px; border: 1px solid #ddd;"><input type="text" class="full-width" data-key="anexo_descripcion" value="${row.anexo_descripcion || ''}" style="width: 100%;"></td>
                 `;
            }
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        iaSuggestionTableContainer.appendChild(table);
    }

    // Helper: Leer datos desde la tabla del modal
    function getModalTableData(targetId) {
        const rows = document.querySelectorAll('#ia-suggestion-table-container table tbody tr');
        const data = [];
        rows.forEach(row => {
            const inputs = row.querySelectorAll('input, textarea');
            const rowData = {};
            inputs.forEach(input => {
                const key = input.getAttribute('data-key');
                if (key) {
                    rowData[key] = input.value;
                }
            });
            data.push(rowData);
        });
        return data;
    }

    // Click en botones IA
    document.querySelectorAll('.btn-ai').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.dataset.target;
            const isTable = this.dataset.type === 'table';
            iaIsTable = isTable;
            iaTargetIdInput.value = targetId;

            let contenido = '';

            if (isTable) {
                contenido = getTableData(targetId);
                iaOriginalData = contenido; // Guardmaos backup/ref
            } else {
                const el = document.getElementById(targetId);
                if (el) contenido = el.value;
            }

            // Validar si hay contenido para procesar
            if ((!isTable && !contenido.trim()) || (isTable && contenido.length === 0)) {
                alert('Por favor, ingresa contenido antes de pedir una sugerencia de la IA.');
                return;
            }

            // UI Loading...
            const originalText = this.innerHTML;
            this.innerHTML = '? Procesando...';
            this.disabled = true;

            // Llamada API
            const requestBody = {
                contexto: getContextData(),
                contenido: contenido,
                campo: targetId,
                es_tabla: isTable
            };

            // Para Documentos Relacionados, añadir Actividades como contexto previo
            if (targetId === 'tabla-documentos') {
                requestBody.contenido_previo = getTableData('tabla-actividades');
            }

            fetch('/api/ia-sugerir', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            })
                .then(response => response.json())
                .then(data => {
                    this.innerHTML = originalText;
                    this.disabled = false;

                    if (data.error) {
                        alert('Error IA: ' + data.error);
                    } else {
                        if (isTable) {
                            try {
                                let parsedData = data.sugerencia;
                                if (typeof parsedData === 'string') {
                                    parsedData = JSON.parse(parsedData);
                                }
                                let tableData = parsedData;

                                // Reset analysis
                                const iaAnalysis = document.getElementById('ia-suggestion-analysis');
                                const iaAnalysisContent = document.getElementById('ia-analysis-content');
                                if (iaAnalysis) iaAnalysis.style.display = 'none';

                                // Check if it's the new structure with analysis
                                if (!Array.isArray(parsedData) && parsedData.nuevos_datos) {
                                    tableData = parsedData.nuevos_datos;
                                    if (parsedData.analisis_general && iaAnalysis) {
                                        iaAnalysisContent.textContent = parsedData.analisis_general;
                                        iaAnalysis.style.display = 'block';
                                    }
                                }

                                renderModalTable(tableData, targetId);

                                // Toggle view
                                iaSuggestionText.style.display = 'none';
                                iaSuggestionTableContainer.style.display = 'block';
                            } catch (e) {
                                console.error("Error al procesar JSON IA:", e);
                                alert("La IA devolvió un formato inválido. Se mostrará como texto.");
                                iaSuggestionText.value = typeof data.sugerencia === 'string' ? data.sugerencia : JSON.stringify(data.sugerencia, null, 2);
                                iaSuggestionText.style.display = 'block';
                                iaSuggestionTableContainer.style.display = 'none';
                            }
                        } else {
                            iaSuggestionText.value = data.sugerencia;
                            iaSuggestionText.style.display = 'block';
                            iaSuggestionTableContainer.style.display = 'none';
                        }
                        iaModal.style.display = 'block';
                    }
                })
                .catch(err => {
                    console.error(err);
                    this.innerHTML = originalText;
                    this.disabled = false;
                    alert('Ocurrió un error al comunicar con la IA.');
                });
        });
    });

    // Aceptar Sugerencia
    if (btnIaAccept) {
        btnIaAccept.addEventListener('click', function () {
            const targetId = iaTargetIdInput.value;
            let nuevosDatos;

            if (iaIsTable && iaSuggestionTableContainer.style.display !== 'none') {
                // Si la tabla es visible, tomamos los datos de ahí
                nuevosDatos = getModalTableData(targetId);
            } else {
                nuevosDatos = iaSuggestionText.value;
            }

            if (iaIsTable) {
                // Modo Tabla: Parsear JSON y reconstruir
                try {
                    if (typeof nuevosDatos === 'string') {
                        nuevosDatos = JSON.parse(nuevosDatos);
                    }

                    if (!Array.isArray(nuevosDatos)) throw new Error('La respuesta no es una lista.');

                    // Limpiar tabla actual
                    const tbody = document.querySelector('#' + targetId + ' tbody');
                    tbody.innerHTML = '';

                    // Reconstruir
                    nuevosDatos.forEach(rowItem => {
                        let htmlRow = '';
                        let numInputName = null;

                        if (targetId === 'tabla-actividades') {
                            htmlRow = '<td><input type="text" name="actividad_no" value="' + (rowItem.actividad_no || '') + '" readonly style="background-color: #eee;"></td>' +
                                '<td><textarea name="actividad_responsable">' + (rowItem.actividad_responsable || '') + '</textarea></td>' +
                                '<td><textarea name="actividad_descripcion">' + (rowItem.actividad_descripcion || '') + '</textarea></td>' +
                                '<td><textarea name="actividad_registro">' + (rowItem.actividad_registro || '') + '</textarea></td>' +
                                '<td><button type="button" class="btn-remove">X</button></td>';
                            numInputName = 'actividad_no';
                        } else if (targetId === 'tabla-documentos') {
                            htmlRow = '<td><input type="text" name="doc_institucional" value="' + (rowItem.doc_institucional || '') + '"></td>' +
                                '<td><input type="text" name="doc_nombre" value="' + (rowItem.doc_nombre || '') + '"></td>' +
                                '<td><input type="text" name="doc_codigo" value="' + (rowItem.doc_codigo || '') + '"></td>' +
                                '<td><button type="button" class="btn-remove">X</button></td>';
                        } else if (targetId === 'tabla-anexos') {
                            htmlRow = '<td><input type="text" name="anexo_no" value="' + (rowItem.anexo_no || '') + '" readonly style="background-color: #eee;"></td>' +
                                '<td><input type="text" name="anexo_nombre" value="' + (rowItem.anexo_nombre || '') + '"></td>' +
                                '<td><input type="text" name="anexo_descripcion" value="' + (rowItem.anexo_descripcion || '') + '"></td>' +
                                '<td><button type="button" class="btn-remove">X</button></td>';
                            numInputName = 'anexo_no';
                        }

                        if (htmlRow) {
                            addTableRow(targetId, htmlRow, numInputName);
                        }
                    });

                    if (targetId === 'tabla-actividades') recalcNumeros(targetId, 'actividad_no');
                    if (targetId === 'tabla-anexos') recalcNumeros(targetId, 'anexo_no');

                } catch (e) {
                    alert('Error al aplicar cambios en tabla. La IA no devolvió un JSON válido: ' + e.message);
                    console.error('JSON Inválido:', nuevosDatos);
                    return;
                }

            } else {
                const el = document.getElementById(targetId);
                if (el) el.value = nuevosDatos;
            }

            closeModalFunc();
        });
    }

    // --- MODAL DRAGGABLE ---
    const modalContent = document.querySelector('#iaModal .modal-content');
    const modalHeader = document.querySelector('#iaModal .modal-header');

    if (modalContent && modalHeader) {
        dragElement(modalContent, modalHeader);
    }

    function dragElement(elmnt, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;

        if (handle) {
            // if present, the header is where you move the DIV from:
            handle.onmousedown = dragMouseDown;
            handle.style.cursor = 'move'; // Visual cue
        } else {
            // otherwise, move the DIV from anywhere inside the DIV:
            elmnt.onmousedown = dragMouseDown;
        }

        function dragMouseDown(e) {
            e = e || window.event;
            // Only drag if left mouse button
            if (e.button !== 0) return;

            e.preventDefault();
            // get the mouse cursor position at startup:
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            // call a function whenever the cursor moves:
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();

            // Check if position is already absolute, if not set it and clear margins to avoid jumps
            const style = window.getComputedStyle(elmnt);
            if (style.position !== 'absolute' && style.position !== 'fixed') {
                elmnt.style.position = 'absolute';
                // Calculate current visual position to set initial top/left correctly
                // This is a bit tricky if it was centered with auto margins.
                // A simpler approach for this specific case might be to just rely on offsetTop/Left
                // assuming the parent is the fullscreen modal overlay.
                elmnt.style.margin = '0';
                // We might need to set initial top/left to current offset
                elmnt.style.top = elmnt.offsetTop + "px";
                elmnt.style.left = elmnt.offsetLeft + "px";
            }

            // calculate the new cursor position:
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;

            // set the element's new position:
            elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
            elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
        }

        function closeDragElement() {
            // stop moving when mouse button is released:
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
});
