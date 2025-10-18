/**
 * InteractiveAudioResize - Custom TipTap Extension for Audio Elements
 * Provides interactive resizing, alignment, and drag-and-drop repositioning for audio elements
 * Following the same pattern as InteractiveImageResize
 */

import { Node, mergeAttributes } from '@tiptap/core';

export const InteractiveAudioResize = Node.create({
  name: 'interactiveAudio',

  group: 'block',

  draggable: true,

  addOptions() {
    return {
      inline: false,
      HTMLAttributes: {
        class: 'interactive-audio',
      },
    };
  },

  addAttributes() {
    return {
      src: {
        default: null,
        parseHTML: element => element.querySelector('audio')?.getAttribute('src'),
        renderHTML: attributes => {
          if (!attributes.src) return {};
          return { src: attributes.src };
        },
      },
      style: {
        default: null,
        parseHTML: element => element.getAttribute('style'),
        renderHTML: attributes => {
          if (!attributes.style) return {};
          return { style: attributes.style };
        },
      },
      class: {
        default: 'interactive-audio audio-center',
        parseHTML: element => element.getAttribute('class'),
        renderHTML: attributes => {
          return { class: attributes.class };
        },
      },
      title: {
        default: null,
        parseHTML: element => element.getAttribute('title'),
        renderHTML: attributes => {
          if (!attributes.title) return {};
          return { title: attributes.title };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="interactive-audio"]',
      },
      {
        tag: 'audio',
        getAttrs: dom => ({
          src: dom.getAttribute('src'),
        }),
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes({ 'data-type': 'interactive-audio' }, HTMLAttributes)];
  },

  addNodeView() {
    return ({ node, getPos, editor }) => {
      const { view } = editor;
      const { src, title, style } = node.attrs;

      let isResizing = false;

      const container = document.createElement('div');
      container.className = 'interactive-audio-container';

      // Function to apply alignment styles to container
      const applyContainerStyles = (nodeAttrs) => {
        let baseStyle = 'position: relative; line-height: 0;';

        const style = (nodeAttrs.style || '').trim();
        if (style.includes('float: left')) {
          const hasExplicitSize = style.includes('width:');
          baseStyle += ' display: inline-block; margin: 0.75rem auto 0.75rem 0; box-sizing: border-box;';
          if (hasExplicitSize) {
            container.classList.add('has-explicit-size');
            baseStyle += ' max-width: 50%;';
          } else {
            baseStyle += ' max-width: 40%;';
            container.classList.remove('has-explicit-size');
          }
        } else if (style.includes('float: right')) {
          const hasExplicitSize = style.includes('width:');
          baseStyle += ' display: inline-block; margin: 0.75rem 0 0.75rem auto; box-sizing: border-box;';
          if (hasExplicitSize) {
            container.classList.add('has-explicit-size');
            baseStyle += ' max-width: 50%;';
          } else {
            baseStyle += ' max-width: 40%;';
            container.classList.remove('has-explicit-size');
          }
        } else if (style.includes('float: none') && (style.includes('display: block') || style.includes('margin:') && style.includes('auto'))) {
          const hasExplicitSize = style.includes('width:');
          baseStyle += ' display: block !important; text-align: center !important; margin: 0.5rem auto !important; max-width: 100% !important;';
          if (hasExplicitSize) {
            container.classList.add('has-explicit-size');
          } else {
            container.classList.remove('has-explicit-size');
          }
        } else if (style.includes('width: 100%') || style.includes('width:100%')) {
          baseStyle += ' display: block; width: 100%; max-width: 100%; margin: 1rem 0;';
        } else {
          baseStyle += ' display: block; max-width: 100%;';
        }

        container.style.cssText = baseStyle;
      };

      applyContainerStyles(node.attrs);

      const audioWrapper = document.createElement('div');
      audioWrapper.className = 'audio-wrapper';
      audioWrapper.style.cssText = `
        position: relative;
        width: 100%;
        min-width: 200px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      `;

      const audio = document.createElement('audio');
      audio.src = src;
      audio.controls = true;
      audio.className = 'w-full';
      audio.style.cssText = 'border-radius: 8px; width: 100%;';
      if (title) audio.title = title;

      // Audio info display
      const audioInfo = document.createElement('div');
      audioInfo.className = 'audio-info';
      audioInfo.style.cssText = `
        margin-top: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 14px;
        gap: 8px;
      `;
      audioInfo.innerHTML = `
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z"/>
        </svg>
        <span>${title || 'Audio File'}</span>
      `;

      audioWrapper.appendChild(audio);
      audioWrapper.appendChild(audioInfo);

      // Apply initial size from attributes
      if (style && style.includes('width:')) {
        const widthMatch = style.match(/width:\s*([^;]+);?/);
        if (widthMatch) {
          audioWrapper.style.setProperty('width', widthMatch[1], 'important');
        }
      }

      const dragHandle = document.createElement('div');
      dragHandle.className = 'drag-handle';
      dragHandle.innerHTML = '✥';
      dragHandle.title = 'Drag to move audio';
      dragHandle.style.cssText = `
        position: absolute; top: 4px; left: 4px; width: 24px; height: 24px;
        background: rgba(102, 126, 234, 0.95); border-radius: 4px; cursor: grab;
        opacity: 0.8; transition: opacity 0.2s ease; z-index: 15; display: flex;
        align-items: center; justify-content: center; color: white; font-size: 14px;
        border: 2px solid rgba(255, 255, 255, 0.8); font-weight: bold;
      `;

      dragHandle.addEventListener('mouseenter', () => {
        dragHandle.style.opacity = '1';
        dragHandle.style.transform = 'scale(1.1)';
      });

      dragHandle.addEventListener('mouseleave', () => {
        dragHandle.style.opacity = '0.8';
        dragHandle.style.transform = 'scale(1)';
      });

      const resizeOverlay = document.createElement('div');
      resizeOverlay.className = 'resize-overlay';
      resizeOverlay.style.cssText = `
        position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0;
        transition: opacity 0.2s ease; border: 2px solid #667eea;
        border-radius: 12px; pointer-events: none; z-index: 1;
      `;

      container.append(audioWrapper, dragHandle, resizeOverlay);

      // --- Drag Logic ---
      let isDragging = false;
      let ghostElement = null;
      let startDragPosInfo = null;

      const startDrag = (e) => {
        if (typeof getPos !== 'function') return;
        const currentPos = getPos();
        if (currentPos === undefined) return;

        e.preventDefault();
        e.stopPropagation();

        isDragging = true;
        startDragPosInfo = { pos: currentPos, node: editor.state.doc.nodeAt(currentPos) };

        editor.setEditable(false);
        dragHandle.style.cursor = 'grabbing';
        container.style.opacity = '0.4';

        ghostElement = audioWrapper.cloneNode(true);
        ghostElement.style.cssText = `
          position: fixed; z-index: 9999; pointer-events: none;
          opacity: 0.7; border: 2px dashed #667eea;
          width: ${audioWrapper.clientWidth}px;
        `;
        document.body.appendChild(ghostElement);

        moveGhost(e);

        document.addEventListener('mousemove', handleDragMove, true);
        document.addEventListener('mouseup', stopDrag, true);
      };

      const handleDragMove = (e) => {
        if (!isDragging) return;
        e.preventDefault();
        e.stopPropagation();
        moveGhost(e);
      };

      const moveGhost = (e) => {
        if (!ghostElement) return;
        ghostElement.style.left = `${e.clientX - ghostElement.clientWidth / 2}px`;
        ghostElement.style.top = `${e.clientY - 50}px`;
      };

      const stopDrag = (e) => {
        if (!isDragging) return;
        e.preventDefault();
        e.stopPropagation();

        isDragging = false;
        editor.setEditable(true);
        dragHandle.style.cursor = 'grab';
        container.style.opacity = '1';
        if (ghostElement) {
          ghostElement.remove();
          ghostElement = null;
        }
        document.removeEventListener('mousemove', handleDragMove, true);
        document.removeEventListener('mouseup', stopDrag, true);

        const dropCoords = { left: e.clientX, top: e.clientY };
        const editorRect = editor.view.dom.getBoundingClientRect();
        const relativeX = dropCoords.left - editorRect.left;
        const editorWidth = editorRect.width;

        let alignment = 'left';
        if (relativeX < editorWidth * 0.25) {
          alignment = 'left';
        } else if (relativeX > editorWidth * 0.75) {
          alignment = 'right';
        } else {
          alignment = 'center';
        }

        if (!startDragPosInfo) return;

        const { pos: originalPos, node: originalNode } = startDragPosInfo;
        startDragPosInfo = null;

        if (originalPos === undefined || !originalNode) return;

        const attrs = { ...originalNode.attrs };
        const currentSize = attrs.style || '';
        const widthMatch = currentSize.match(/width:\s*([^;]+);?/);
        const hasExplicitDimensions = widthMatch !== null;

        let classNames = `interactive-audio audio-${alignment}`;
        if (hasExplicitDimensions) {
          classNames += ' has-explicit-size';
        }
        attrs.class = classNames;

        let alignmentStyle = '';
        if (alignment === 'left') {
          alignmentStyle = 'display: inline-block; margin: 0.75rem auto 0.75rem 0; box-sizing: border-box;';
        } else if (alignment === 'right') {
          alignmentStyle = 'display: inline-block; margin: 0.75rem 0 0.75rem auto; box-sizing: border-box;';
        } else if (alignment === 'center') {
          alignmentStyle = 'float: none; display: block; margin: 0.5rem auto;';
        }

        let sizeStyle = '';
        if (widthMatch) {
          sizeStyle = `width: ${widthMatch[1]};`;
        }

        attrs.style = (alignmentStyle + (sizeStyle ? ' ' + sizeStyle : '')).trim();

        const { tr } = editor.state;
        tr.setNodeMarkup(originalPos, undefined, attrs);
        editor.view.dispatch(tr);
      };

      dragHandle.addEventListener('mousedown', startDrag);

      // --- Resize Logic ---
      const handles = [
        { pos: 'w', cursor: 'w-resize' }, { pos: 'e', cursor: 'e-resize' }
      ];

      handles.forEach(({ pos, cursor }) => {
        const handle = document.createElement('div');
        handle.className = `resize-handle resize-handle-${pos}`;
        handle.style.cursor = cursor;
        handle.style.cssText += `
          position: absolute; width: 12px; height: 12px; background: #667eea;
          border: 2px solid white; border-radius: 50%; pointer-events: auto; z-index: 10;
        `;
        const s = handle.style;
        s.top = '50%';
        s.transform = 'translateY(-50%)';
        if (pos === 'w') s.left = '-6px';
        if (pos === 'e') s.right = '-6px';

        let startX, startWidth;

        const startResize = (e) => {
          e.preventDefault();
          e.stopPropagation();
          isResizing = true;
          editor.setEditable(false);
          const rect = audioWrapper.getBoundingClientRect();
          startX = e.clientX;
          startWidth = rect.width;
          document.body.style.cursor = cursor;
          document.body.style.userSelect = 'none';
          document.addEventListener('mousemove', handleResize, true);
          document.addEventListener('mouseup', stopResize, true);
        };

        const handleResize = (e) => {
          if (!isResizing) return;
          e.preventDefault();

          const deltaX = e.clientX - startX;
          let newWidth = startWidth;

          if (pos === 'e') newWidth = startWidth + deltaX;
          if (pos === 'w') newWidth = startWidth - deltaX;

          audioWrapper.style.width = `${Math.max(200, newWidth)}px`;
        };

        const stopResize = () => {
          if (!isResizing) return;
          isResizing = false;
          editor.setEditable(true);
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          document.removeEventListener('mousemove', handleResize, true);
          document.removeEventListener('mouseup', stopResize, true);

          const finalWidth = parseFloat(audioWrapper.style.width);

          if (typeof getPos === 'function') {
            const currentAttrs = { ...node.attrs };
            const existingStyle = currentAttrs.style || '';

            let updatedStyle = existingStyle.replace(/width:\s*[^;]+;?/g, '');
            updatedStyle = `${updatedStyle} width: ${finalWidth}px !important;`.replace(/\s+/g, ' ').trim();

            let currentClass = currentAttrs.class || '';
            if (!currentClass.includes('has-explicit-size')) {
              currentClass = `${currentClass} has-explicit-size`.trim();
            }

            const newAttrs = {
              ...currentAttrs,
              style: updatedStyle,
              class: currentClass,
            };

            editor.view.dispatch(
              editor.state.tr.setNodeMarkup(getPos(), undefined, newAttrs)
            );
          }
        };

        handle.addEventListener('mousedown', startResize);
        resizeOverlay.appendChild(handle);
      });

      // --- Hover effects ---
      container.addEventListener('mouseenter', () => {
        if (!isDragging && !document.querySelector('.resize-handle:active')) {
          dragHandle.style.opacity = '1';
          resizeOverlay.style.opacity = '1';
        }
      });
      container.addEventListener('mouseleave', () => {
        if (!isDragging && !document.querySelector('.resize-handle:active')) {
          dragHandle.style.opacity = '0.8';
          resizeOverlay.style.opacity = '0';
        }
      });

      return {
        dom: container,
        update: (updatedNode) => {
          if (updatedNode.type.name !== this.name) return false;
          audio.src = updatedNode.attrs.src;
          if (updatedNode.attrs.title) {
            audio.title = updatedNode.attrs.title;
            audioInfo.querySelector('span').textContent = updatedNode.attrs.title;
          }

          applyContainerStyles(updatedNode.attrs);

          if (updatedNode.attrs.style && !isResizing) {
            const styleString = updatedNode.attrs.style;
            const widthMatch = styleString.match(/width:\s*([^;]+);?/);
            if (widthMatch) {
              audioWrapper.style.setProperty('width', widthMatch[1], 'important');
              container.classList.add('has-explicit-size');
            }
          }

          const audioClass = updatedNode.attrs.class || '';
          container.className = 'interactive-audio-container';
          if (audioClass.includes('audio-left')) {
            container.classList.add('audio-left');
          } else if (audioClass.includes('audio-right')) {
            container.classList.add('audio-right');
          } else if (audioClass.includes('audio-center')) {
            container.classList.add('audio-center');
          } else if (audioClass.includes('audio-full')) {
            container.classList.add('audio-full');
          }

          return true;
        },
        destroy: () => {
          container.remove();
          document.removeEventListener('mousemove', handleDragMove, true);
          document.removeEventListener('mouseup', stopDrag, true);
        },
      };
    };
  },
});

export default InteractiveAudioResize;
