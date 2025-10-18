/**
 * InteractiveVideoResize - Custom TipTap Extension for Video Elements
 * Provides interactive resizing, alignment, and drag-and-drop repositioning for video elements
 * Following the same pattern as InteractiveImageResize
 */

import { Node, mergeAttributes } from '@tiptap/core';

export const InteractiveVideoResize = Node.create({
  name: 'interactiveVideo',

  group: 'block',

  draggable: true,

  addOptions() {
    return {
      inline: false,
      HTMLAttributes: {
        class: 'interactive-video',
      },
    };
  },

  addAttributes() {
    return {
      src: {
        default: null,
        parseHTML: element => element.querySelector('video')?.getAttribute('src'),
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
        default: 'interactive-video video-center',
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
      poster: {
        default: null,
        parseHTML: element => element.querySelector('video')?.getAttribute('poster'),
        renderHTML: attributes => {
          if (!attributes.poster) return {};
          return { poster: attributes.poster };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="interactive-video"]',
      },
      {
        tag: 'video',
        getAttrs: dom => ({
          src: dom.getAttribute('src'),
          poster: dom.getAttribute('poster'),
        }),
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes({ 'data-type': 'interactive-video' }, HTMLAttributes)];
  },

  addNodeView() {
    return ({ node, getPos, editor }) => {
      const { view } = editor;
      const { src, title, style, poster } = node.attrs;

      let isResizing = false;

      const container = document.createElement('div');
      container.className = 'interactive-video-container';

      // Function to apply alignment styles to container
      const applyContainerStyles = (nodeAttrs) => {
        let baseStyle = 'position: relative; line-height: 0;';

        const style = (nodeAttrs.style || '').trim();
        if (style.includes('float: left')) {
          const hasExplicitSize = style.includes('width:') && style.includes('height:');
          baseStyle += ' display: inline-block; margin: 0.75rem auto 0.75rem 0; box-sizing: border-box;';
          if (hasExplicitSize) {
            container.classList.add('has-explicit-size');
            baseStyle += ' max-width: 50%;';
          } else {
            baseStyle += ' max-width: 40%;';
            container.classList.remove('has-explicit-size');
          }
        } else if (style.includes('float: right')) {
          const hasExplicitSize = style.includes('width:') && style.includes('height:');
          baseStyle += ' display: inline-block; margin: 0.75rem 0 0.75rem auto; box-sizing: border-box;';
          if (hasExplicitSize) {
            container.classList.add('has-explicit-size');
            baseStyle += ' max-width: 50%;';
          } else {
            baseStyle += ' max-width: 40%;';
            container.classList.remove('has-explicit-size');
          }
        } else if (style.includes('float: none') && (style.includes('display: block') || style.includes('margin:') && style.includes('auto'))) {
          const hasExplicitSize = style.includes('width:') && style.includes('height:');
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

      const video = document.createElement('video');
      video.src = src;
      video.controls = true;
      video.className = 'max-w-full h-auto rounded-lg';
      if (title) video.title = title;
      if (poster) video.poster = poster;
      video.style.cssText = 'display: block; user-select: none; border-radius: 0.5rem;';

      // Apply initial size from attributes
      if (style) {
        const styleProps = style.split(';').filter(prop => prop.trim());
        styleProps.forEach(prop => {
          const [property, value] = prop.split(':').map(s => s.trim());
          if (property && value) {
            if (property === 'width' || property === 'height') {
              video.style.setProperty(property, value, 'important');
            } else {
              video.style.setProperty(property, value);
            }
          }
        });
      }

      const dragHandle = document.createElement('div');
      dragHandle.className = 'drag-handle';
      dragHandle.innerHTML = '✥';
      dragHandle.title = 'Drag to move video';
      dragHandle.style.cssText = `
        position: absolute; top: 4px; left: 4px; width: 24px; height: 24px;
        background: rgba(239, 68, 68, 0.95); border-radius: 4px; cursor: grab;
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
        transition: opacity 0.2s ease; border: 2px solid #ef4444;
        border-radius: 8px; pointer-events: none; z-index: 1;
      `;

      container.append(video, dragHandle, resizeOverlay);

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

        ghostElement = video.cloneNode();
        ghostElement.style.cssText = `
          position: fixed; z-index: 9999; pointer-events: none;
          opacity: 0.7; border: 2px dashed #ef4444;
          width: ${video.clientWidth}px; height: ${video.clientHeight}px;
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
        ghostElement.style.top = `${e.clientY - ghostElement.clientHeight / 2}px`;
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
        const heightMatch = currentSize.match(/height:\s*([^;]+);?/);
        const hasExplicitDimensions = widthMatch !== null || heightMatch !== null;

        let classNames = `interactive-video video-${alignment}`;
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
        if (widthMatch && heightMatch) {
          sizeStyle = `width: ${widthMatch[1]}; height: ${heightMatch[1]};`;
        } else if (widthMatch) {
          sizeStyle = `width: ${widthMatch[1]};`;
        } else if (heightMatch) {
          sizeStyle = `height: ${heightMatch[1]};`;
        }

        attrs.style = (alignmentStyle + (sizeStyle ? ' ' + sizeStyle : '')).trim();

        const { tr } = editor.state;
        tr.setNodeMarkup(originalPos, undefined, attrs);
        editor.view.dispatch(tr);
      };

      dragHandle.addEventListener('mousedown', startDrag);

      // --- Resize Logic ---
      const handles = [
        { pos: 'nw', cursor: 'nw-resize' }, { pos: 'ne', cursor: 'ne-resize' },
        { pos: 'sw', cursor: 'sw-resize' }, { pos: 'se', cursor: 'se-resize' },
        { pos: 'n', cursor: 'n-resize' }, { pos: 's', cursor: 's-resize' },
        { pos: 'w', cursor: 'w-resize' }, { pos: 'e', cursor: 'e-resize' }
      ];

      handles.forEach(({ pos, cursor }) => {
        const handle = document.createElement('div');
        handle.className = `resize-handle resize-handle-${pos}`;
        handle.style.cursor = cursor;
        handle.style.cssText += `
          position: absolute; width: 12px; height: 12px; background: #ef4444;
          border: 2px solid white; border-radius: 50%; pointer-events: auto; z-index: 10;
        `;
        const s = handle.style;
        if (pos.includes('n')) s.top = '-6px';
        if (pos.includes('s')) s.bottom = '-6px';
        if (pos.includes('w')) s.left = '-6px';
        if (pos.includes('e')) s.right = '-6px';
        if (pos === 'n' || pos === 's') { s.left = '50%'; s.transform = 'translateX(-50%)'; }
        if (pos === 'w' || pos === 'e') { s.top = '50%'; s.transform = 'translateY(-50%)'; }

        let startX, startY, startWidth, startHeight, aspectRatio;

        const startResize = (e) => {
          e.preventDefault();
          e.stopPropagation();
          isResizing = true;
          editor.setEditable(false);
          const rect = video.getBoundingClientRect();
          startX = e.clientX;
          startY = e.clientY;
          startWidth = rect.width;
          startHeight = rect.height;
          aspectRatio = startWidth / startHeight;
          document.body.style.cursor = cursor;
          document.body.style.userSelect = 'none';
          document.addEventListener('mousemove', handleResize, true);
          document.addEventListener('mouseup', stopResize, true);
        };

        const handleResize = (e) => {
          if (!isResizing) return;
          e.preventDefault();

          const deltaX = e.clientX - startX;
          const deltaY = e.clientY - startY;
          let newWidth = startWidth;
          let newHeight = startHeight;

          if (pos.includes('e')) newWidth = startWidth + deltaX;
          if (pos.includes('w')) newWidth = startWidth - deltaX;
          if (pos.includes('s')) newHeight = startHeight + deltaY;
          if (pos.includes('n')) newHeight = startHeight - deltaY;

          // Maintain aspect ratio
          if (pos.length === 2) { // Corner handles
            if (Math.abs(deltaX) > Math.abs(deltaY)) {
              newHeight = newWidth / aspectRatio;
            } else {
              newWidth = newHeight * aspectRatio;
            }
          } else if (pos === 'n' || pos === 's') {
            newWidth = newHeight * aspectRatio;
          } else {
            newHeight = newWidth / aspectRatio;
          }

          video.style.width = `${Math.max(200, newWidth)}px`;
          video.style.height = `${Math.max(112, newHeight)}px`; // 16:9 minimum
        };

        const stopResize = () => {
          if (!isResizing) return;
          isResizing = false;
          editor.setEditable(true);
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          document.removeEventListener('mousemove', handleResize, true);
          document.removeEventListener('mouseup', stopResize, true);

          const finalWidth = parseFloat(video.style.width);
          const finalHeight = parseFloat(video.style.height);

          if (typeof getPos === 'function') {
            const currentAttrs = { ...node.attrs };
            const existingStyle = currentAttrs.style || '';

            let updatedStyle = existingStyle.replace(/width:\s*[^;]+;?/g, '').replace(/height:\s*[^;]+;?/g, '');
            updatedStyle = `${updatedStyle} width: ${finalWidth}px !important; height: ${finalHeight}px !important;`.replace(/\s+/g, ' ').trim();

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
          video.src = updatedNode.attrs.src;
          if (updatedNode.attrs.title) video.title = updatedNode.attrs.title;
          if (updatedNode.attrs.poster) video.poster = updatedNode.attrs.poster;

          applyContainerStyles(updatedNode.attrs);

          const style = updatedNode.attrs.style || '';
          const hasExplicitSize = style.match(/width:\s*\d+px[^;]*;?\s*height:\s*\d+px[^;]*;?/);

          if (style.includes('float: left') || style.includes('float: right')) {
            if (hasExplicitSize) {
              container.classList.add('has-explicit-size');
            } else {
              container.classList.remove('has-explicit-size');
            }
          } else if (style.includes('float: none') && (style.includes('display: block') || style.includes('margin:') && style.includes('auto'))) {
            if (hasExplicitSize) {
              container.classList.add('has-explicit-size');
            } else {
              container.classList.remove('has-explicit-size');
            }
            video.style.setProperty('display', 'block', 'important');
            video.style.setProperty('margin', '0 auto', 'important');
          } else {
            video.style.setProperty('display', 'block', 'important');
            video.style.removeProperty('margin');
            container.classList.remove('has-explicit-size');
          }

          if (updatedNode.attrs.style && !isResizing) {
            const styleString = updatedNode.attrs.style;
            const styleProps = styleString.split(';').filter(prop => prop.trim());

            let hasWidth = false, hasHeight = false;

            styleProps.forEach(prop => {
              const [property, value] = prop.split(':').map(s => s.trim());
              if (property && value) {
                if (property === 'width') {
                  video.style.setProperty(property, value, 'important');
                  hasWidth = true;
                } else if (property === 'height') {
                  video.style.setProperty(property, value, 'important');
                  hasHeight = true;
                }
              }
            });

            if (hasWidth && hasHeight) {
              container.classList.add('has-explicit-size');
            }

            video.style.userSelect = 'none';
          }

          const videoClass = updatedNode.attrs.class || '';
          container.className = 'interactive-video-container';
          if (videoClass.includes('video-left')) {
            container.classList.add('video-left');
          } else if (videoClass.includes('video-right')) {
            container.classList.add('video-right');
          } else if (videoClass.includes('video-center')) {
            container.classList.add('video-center');
          } else if (videoClass.includes('video-full')) {
            container.classList.add('video-full');
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

export default InteractiveVideoResize;
