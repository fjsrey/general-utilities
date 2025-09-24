/**
 * TableColumnReorder
 * -------------------
 * Librería para permitir reordenar columnas de una tabla HTML por drag & drop.
 * Guarda el orden en localStorage para mantenerlo entre sesiones.
 *
 * OPCIONES:
 * - useClass: true para indicar columnas reordenables por clase CSS (ej. class="reorder")
 * - className: nombre de la clase CSS que indica columnas reordenables
 * - allowedIndexes: array de índices de columna permitidas (ignora clases CSS si se define)
 * - allowDropBetweenUnmovable: true para permitir soltar entre dos columnas no reordenables (por defecto: false)
 *
 * USO:
 * new TableColumnReorder('miTabla', {
 *   useClass: true,
 *   className: 'reorder',
 *   allowDropBetweenUnmovable: false
 * });
 */
class TableColumnReorder {
  constructor(tableId, options = {}) {
    this.table = document.getElementById(tableId);
    if (!this.table || !this.table.tHead || !this.table.tHead.rows.length) {
      console.error('Tabla no válida o sin encabezado.');
      return;
    }

    this.storageKey = `table_column_order_${tableId}`;
    this.dragSrcIndex = null;

    this.options = {
      useClass: options.useClass || false,
      className: options.className || 'reorder',
      allowedIndexes: Array.isArray(options.allowedIndexes) ? options.allowedIndexes : null,
      allowDropBetweenUnmovable: !!options.allowDropBetweenUnmovable
    };

    this.allowedColumnIds = null;
    this.init();
  }

  init() {
    if (this.options.allowedIndexes !== null) {
      this.mapAllowedIndexesToColumnIds();
    }
    this.restoreColumnOrder();
    this.setupDragEvents();
  }

  mapAllowedIndexesToColumnIds() {
    const headerCells = this.table.tHead.rows[0].cells;
    this.allowedColumnIds = this.options.allowedIndexes
      .map(i => this.getColumnId(headerCells[i]))
      .filter(id => id !== null);
  }

  getColumnId(cell) {
    if (!cell) return null;
    return cell.getAttribute('data-col-index') || cell.textContent.trim();
  }

  isColumnReorderable(cell) {
    const colId = this.getColumnId(cell);
    if (!colId) return false;

    if (this.allowedColumnIds !== null) {
      return this.allowedColumnIds.includes(colId);
    }

    if (this.options.useClass) {
      return cell.classList.contains(this.options.className);
    }

    return true;
  }

  setupDragEvents() {
    const headerCells = this.table.tHead.rows[0].cells;

    Array.from(headerCells).forEach((cell) => {
      if (this.isColumnReorderable(cell)) {
        cell.setAttribute('draggable', true);

        cell.addEventListener('dragstart', (e) => {
          const th = e.target.closest('th');
          if (!this.isColumnReorderable(th)) {
            e.preventDefault();
            return;
          }
          this.dragSrcIndex = Array.from(th.parentNode.children).indexOf(th);
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', this.dragSrcIndex);
        });

        cell.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
        });

        cell.addEventListener('drop', (e) => {
          e.preventDefault();
          const targetTh = e.target.closest('th');
          if (!targetTh) return;

          const destIndex = Array.from(targetTh.parentNode.children).indexOf(targetTh);
          const headerCellsArray = Array.from(this.table.tHead.rows[0].cells);
          const srcIndex = this.dragSrcIndex;

          if (srcIndex === null || destIndex === null || srcIndex === destIndex) return;

          const fromCell = headerCellsArray[srcIndex];
          const toCell = headerCellsArray[destIndex];

          if (!this.isColumnReorderable(fromCell) || !this.isColumnReorderable(toCell)) return;

          if (!this.options.allowDropBetweenUnmovable) {
            const min = Math.min(srcIndex, destIndex);
            const max = Math.max(srcIndex, destIndex);

            const leftCell = headerCellsArray[min - 1];
            const rightCell = headerCellsArray[max + 1];

            const leftMovable = leftCell ? this.isColumnReorderable(leftCell) : true;
            const rightMovable = rightCell ? this.isColumnReorderable(rightCell) : true;

            if (!leftMovable && !rightMovable) {
              console.warn('No se puede soltar entre dos columnas no reordenables.');
              return;
            }
          }

          this.moveColumn(srcIndex, destIndex);
          this.saveColumnOrder();
          this.dragSrcIndex = null;
        });
      } else {
        cell.removeAttribute('draggable');
      }
    });
  }

  moveColumn(fromIndex, toIndex) {
    const rows = this.table.rows;
    for (let row of rows) {
      const cells = Array.from(row.cells);
      const movedCell = cells[fromIndex];
      if (!movedCell) continue;

      if (fromIndex < toIndex) {
        row.insertBefore(movedCell, cells[toIndex + 1]);
      } else {
        row.insertBefore(movedCell, cells[toIndex]);
      }
    }
  }

  getCurrentColumnOrder() {
    return Array.from(this.table.tHead.rows[0].cells).map(cell => this.getColumnId(cell));
  }

  saveColumnOrder() {
    const headers = this.getCurrentColumnOrder();
    localStorage.setItem(this.storageKey, JSON.stringify(headers));
  }

  restoreColumnOrder() {
    const savedOrder = localStorage.getItem(this.storageKey);
    if (!savedOrder) return;

    const savedIds = JSON.parse(savedOrder);
    const currentCells = Array.from(this.table.tHead.rows[0].cells);
    const currentIds = currentCells.map(cell => this.getColumnId(cell));

    for (let targetIndex = 0; targetIndex < savedIds.length; targetIndex++) {
      const colId = savedIds[targetIndex];
      const currentIndex = currentIds.indexOf(colId);
      if (currentIndex === -1 || currentIndex === targetIndex) continue;

      this.moveColumn(currentIndex, targetIndex);

      const moved = currentIds.splice(currentIndex, 1)[0];
      currentIds.splice(targetIndex, 0, moved);
    }
  }
}
