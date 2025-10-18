import React, { useCallback, useMemo, useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Placeholder } from '@tiptap/extension-placeholder';
import { Link } from '@tiptap/extension-link';
import { CharacterCount } from '@tiptap/extension-character-count';
import { TextStyle } from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import { Highlight } from '@tiptap/extension-highlight';
import { TextAlign } from '@tiptap/extension-text-align';
import { Underline } from '@tiptap/extension-underline';
import { Subscript } from '@tiptap/extension-subscript';
import { Superscript } from '@tiptap/extension-superscript';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableHeader } from '@tiptap/extension-table-header';
import { TableCell } from '@tiptap/extension-table-cell';
import { TaskList } from '@tiptap/extension-task-list';
import { TaskItem } from '@tiptap/extension-task-item';
import { Image } from '@tiptap/extension-image';
import { CodeBlock } from '@tiptap/extension-code-block';
import { HorizontalRule } from '@tiptap/extension-horizontal-rule';
import { Typography } from '@tiptap/extension-typography';
import Focus from '@tiptap/extension-focus';
import { Dropcursor } from '@tiptap/extension-dropcursor';
import { Mention } from '@tiptap/extension-mention';
import { socialAPI } from '../../services/social-api';
import { InteractiveAudioResize } from './tiptap-extensions/InteractiveAudioResize';
import { InteractiveVideoResize } from './tiptap-extensions/InteractiveVideoResize';

// Heroicons (outline) used in toolbar
import {
  CodeBracketIcon,
  ListBulletIcon,
  ChatBubbleLeftRightIcon,
  LinkIcon,
  XMarkIcon,
  SwatchIcon,
  PaintBrushIcon,
  TableCellsIcon,
  CheckIcon,
  PhotoIcon,
  MinusIcon,
  Bars3BottomLeftIcon,
  Bars3Icon,
  Bars3BottomRightIcon,
  Bars4Icon,
  DocumentTextIcon,
  CubeIcon,
  SparklesIcon,
  PlusIcon,
  TrashIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  CloudArrowUpIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ArrowUturnLeftIcon,
  ArrowUturnRightIcon,
  MusicalNoteIcon,
  PaperClipIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  FaceSmileIcon
} from '@heroicons/react/24/outline';

// Media type accept constants (added to fix ReferenceError in upload handlers)
const ACCEPT_IMAGE = [
  'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/avif', 'image/jpg'
];
const ACCEPT_VIDEO = [
  'video/mp4', 'video/webm', 'video/ogg'
];
const ACCEPT_AUDIO = [
  'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/webm'
];
const ACCEPT_PDF = [
  'application/pdf'
];

// Inline fallback icons for formatting actions not provided by Heroicons
const iconBase = 'w-4 h-4 fill-current';
export const BoldIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M7 4h6a4 4 0 0 1 0 8H7V4Zm0 8h7a4 4 0 0 1 0 8H7v-8Z" />
  </svg>
);
export const ItalicIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M10 4v3h2.21l-3.42 10H6v3h8v-3h-2.21l3.42-10H18V4h-8Z" />
  </svg>
);
export const StrikethroughIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M4 11v2h7v4h2v-4h7v-2H4Zm4.5-2c0-1.1.9-2 2.9-2 1.38 0 2.57.42 3.6 1.26L16.5 5C15.04 3.74 13.16 3 11.4 3 8.26 3 6.5 4.96 6.5 7h2Z" />
  </svg>
);
export const UnderlineIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M6 3v8a6 6 0 0 0 12 0V3h-2.5v8a3.5 3.5 0 0 1-7 0V3H6Zm-1 16v2h14v-2H5Z" />
  </svg>
);

// Interactive Image Resize Extension
const InteractiveImageResize = Image.extend({
  name: 'interactiveImage',

  addOptions() {
    return {
      ...this.parent?.(),
      inline: true,  // Changed from false to true for inline behavior
      allowBase64: true,
      HTMLAttributes: {
        class: 'max-w-full h-auto rounded-lg',
      },
    };
  },

  addAttributes() {
    return {
      ...this.parent?.(),
      style: {
        default: null,
        parseHTML: element => element.getAttribute('style'),
        renderHTML: attributes => {
          if (!attributes.style) return {};
          return { style: attributes.style };
        },
      },
      class: {
        default: 'max-w-full h-auto rounded-lg',
        parseHTML: element => element.getAttribute('class'),
        renderHTML: attributes => {
          return { class: attributes.class };
        },
      },
    };
  },

  addNodeView() {
    return ({ node, getPos, editor }) => {
      const { view } = editor;
      const { src, alt, title, style } = node.attrs;

      // Define isResizing at the top level so it's accessible everywhere
      let isResizing = false;

      const container = document.createElement('div');
      container.className = 'interactive-image-container';

      // Function to apply alignment styles to container
      const applyContainerStyles = (nodeAttrs) => {
        let baseStyle = 'position: relative; line-height: 0;';

        // Extract alignment from style attribute
        const style = (nodeAttrs.style || '').trim();
        if (style.includes('float: left')) {
          const hasExplicitSize = style.includes('width:') && style.includes('height:');
          baseStyle += ' display: inline-block; margin: 0.75rem auto 0.75rem 0; box-sizing: border-box;';
          if (hasExplicitSize) {
            container.classList.add('has-explicit-size');
            baseStyle += ' max-width: 50%;'; // Constrain even with explicit size
          } else {
            baseStyle += ' max-width: 40%;';
            container.classList.remove('has-explicit-size');
          }
        } else if (style.includes('float: right')) {
          const hasExplicitSize = style.includes('width:') && style.includes('height:');
          baseStyle += ' display: inline-block; margin: 0.75rem 0 0.75rem auto; box-sizing: border-box;';
          if (hasExplicitSize) {
            container.classList.add('has-explicit-size');
            baseStyle += ' max-width: 50%;'; // Constrain even with explicit size
          } else {
            baseStyle += ' max-width: 40%;';
            container.classList.remove('has-explicit-size');
          }
        } else if ((style.includes('float: none') && style.includes('display: block') && style.includes('margin:') && style.includes('auto')) ||
                   (style.includes('max-width: 100%') && style.includes('float: none')) ||
                   (style.includes('max-width: 80%') && style.includes('float: none'))) {
          // For center alignment, don't over-constrain
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
          baseStyle += ' display: inline-block; max-width: 100%;';
        }

        container.style.cssText = baseStyle;
      };

      // Apply initial alignment
      applyContainerStyles(node.attrs);

      const img = document.createElement('img');
      img.src = src;
      img.alt = alt || '';
      img.title = title || '';
      img.className = node.attrs.class || 'max-w-full h-auto rounded-lg';
      img.draggable = false; // Disable native drag on the image itself
      img.style.userSelect = 'none';

      // Set initial display based on alignment
      const initialStyle = node.attrs.style || '';
      if (initialStyle.includes('float: none') && initialStyle.includes('max-width: 80%') && !initialStyle.includes('width: 100%')) {
        img.style.display = 'inline-block'; // For center alignment
      } else {
        img.style.display = 'block'; // For other alignments
      }

      // Apply initial size from attributes with proper priority
      if (style) {
        // Parse and apply individual style properties
        const styleProps = style.split(';').filter(prop => prop.trim());
        styleProps.forEach(prop => {
          const [property, value] = prop.split(':').map(s => s.trim());
          if (property && value) {
            if (property === 'width' || property === 'height') {
              // Apply dimensions with !important to override CSS
              img.style.setProperty(property, value, 'important');
            } else {
              // Apply other styles normally
              img.style.setProperty(property, value);
            }
          }
        });
      }

      const dragHandle = document.createElement('div');
      dragHandle.className = 'drag-handle';
      dragHandle.innerHTML = '✥';
      dragHandle.title = 'Drag to move image';
      dragHandle.style.cssText = `
        position: absolute; top: 4px; left: 4px; width: 24px; height: 24px;
        background: rgba(59, 130, 246, 0.95); border-radius: 4px; cursor: grab;
        opacity: 0.8; transition: opacity 0.2s ease; z-index: 15; display: flex;
        align-items: center; justify-content: center; color: white; font-size: 14px;
        border: 2px solid rgba(255, 255, 255, 0.8); font-weight: bold;
      `;

      // Make sure drag handle is always visible for debugging
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
        transition: opacity 0.2s ease; border: 2px solid #3b82f6;
        border-radius: 8px; pointer-events: none; z-index: 1;
      `;

      container.append(img, dragHandle, resizeOverlay);

      // --- Drag Logic ---
      let isDragging = false;
      let ghostImage = null;
      let startDragPosInfo = null; // Will store { pos, node }

      const startDrag = (e) => {
        if (typeof getPos !== 'function') return;
        const currentPos = getPos();
        if (currentPos === undefined) return;

        e.preventDefault();
        e.stopPropagation();

        isDragging = true;
        // Store the node and its starting position
        startDragPosInfo = { pos: currentPos, node: editor.state.doc.nodeAt(currentPos) };

        editor.setEditable(false);
        dragHandle.style.cursor = 'grabbing';
        container.style.opacity = '0.4';

        // Create ghost image
        ghostImage = img.cloneNode();
        ghostImage.style.cssText = `
          position: fixed; z-index: 9999; pointer-events: none;
          opacity: 0.7; border: 2px dashed #3b82f6;
          width: ${img.clientWidth}px; height: ${img.clientHeight}px;
        `;
        document.body.appendChild(ghostImage);

        moveGhost(e); // Position ghost on start

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
        if (!ghostImage) return;
        ghostImage.style.left = `${e.clientX - ghostImage.width / 2}px`;
        ghostImage.style.top = `${e.clientY - ghostImage.height / 2}px`;
      };

      const stopDrag = (e) => {
        if (!isDragging) return;
        e.preventDefault();
        e.stopPropagation();

        // Cleanup UI
        isDragging = false;
        editor.setEditable(true);
        dragHandle.style.cursor = 'grab';
        container.style.opacity = '1';
        if (ghostImage) {
          ghostImage.remove();
          ghostImage = null;
        }
        document.removeEventListener('mousemove', handleDragMove, true);
        document.removeEventListener('mouseup', stopDrag, true);

        // --- Core Logic ---
        const dropCoords = { left: e.clientX, top: e.clientY };

        // Get the editor container bounds to determine alignment
        const editorRect = editor.view.dom.getBoundingClientRect();
        const relativeX = dropCoords.left - editorRect.left;
        const editorWidth = editorRect.width;

        // Determine alignment based on drop position within editor
        let alignment = 'left'; // default
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

        // Instead of moving the image, apply alignment styling
        const attrs = { ...originalNode.attrs };

        // Extract existing dimensions first
        const currentSize = attrs.style || '';
        const widthMatch = currentSize.match(/width:\s*([^;]+);?/);
        const heightMatch = currentSize.match(/height:\s*([^;]+);?/);
        const hasExplicitDimensions = widthMatch !== null || heightMatch !== null;

        // Set class with has-explicit-size if dimensions exist
        let classNames = `max-w-full h-auto rounded-lg image-${alignment}`;
        if (hasExplicitDimensions) {
          classNames += ' has-explicit-size';
        }
        attrs.class = classNames;

        // Add alignment styles - content uses float, preview would use float:none (but this is content context)
        let alignmentStyle = '';
        if (alignment === 'left') {
          // Use margin-based positioning to avoid crossing preview boundaries
          alignmentStyle = 'display: inline-block; margin: 0.75rem auto 0.75rem 0; box-sizing: border-box;';
        } else if (alignment === 'right') {
          // Use margin-based positioning to avoid crossing preview boundaries
          alignmentStyle = 'display: inline-block; margin: 0.75rem 0 0.75rem auto; box-sizing: border-box;';
        } else if (alignment === 'center') {
          alignmentStyle = 'float: none; display: block; margin: 0.5rem auto;';
        }

        // Preserve existing size styles - put them after alignment styles
        let sizeStyle = '';
        if (widthMatch && heightMatch) {
          sizeStyle = `width: ${widthMatch[1]}; height: ${heightMatch[1]};`;
        } else if (widthMatch) {
          sizeStyle = `width: ${widthMatch[1]};`;
        } else if (heightMatch) {
          sizeStyle = `height: ${heightMatch[1]};`;
        }

        // Combine styles: alignment first, then size to preserve dimensions
        attrs.style = (alignmentStyle + (sizeStyle ? ' ' + sizeStyle : '')).trim();

        // Apply the alignment change to the existing image
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
          position: absolute; width: 12px; height: 12px; background: #3b82f6;
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
          const rect = img.getBoundingClientRect();
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

          img.style.width = `${Math.max(30, newWidth)}px`;
          img.style.height = `${Math.max(30, newHeight)}px`;
        };

        const stopResize = () => {
          if (!isResizing) return;
          isResizing = false;
          editor.setEditable(true);
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          document.removeEventListener('mousemove', handleResize, true);
          document.removeEventListener('mouseup', stopResize, true);

          const finalWidth = parseFloat(img.style.width);
          const finalHeight = parseFloat(img.style.height);

          if (typeof getPos === 'function') {
            const currentAttrs = { ...node.attrs };

            // Preserve existing alignment styles but update size
            const existingStyle = currentAttrs.style || '';

            // Remove old width/height and add new ones with !important
            let updatedStyle = existingStyle.replace(/width:\s*[^;]+;?/g, '').replace(/height:\s*[^;]+;?/g, '');
            updatedStyle = `${updatedStyle} width: ${finalWidth}px !important; height: ${finalHeight}px !important;`.replace(/\s+/g, ' ').trim();

            // Add has-explicit-size class to existing classes
            let currentClass = currentAttrs.class || '';
            if (!currentClass.includes('has-explicit-size')) {
              currentClass = `${currentClass} has-explicit-size`.trim();
            }

            const newAttrs = {
              ...currentAttrs,
              style: updatedStyle,
              class: currentClass,
            };

            // Dispatch the update to preserve the new dimensions
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
          dragHandle.style.opacity = '0.8'; // Keep it visible
          resizeOverlay.style.opacity = '0';
        }
      });

      return {
        dom: container,
        update: (updatedNode) => {
          if (updatedNode.type.name !== this.name) return false;
          img.src = updatedNode.attrs.src;
          img.alt = updatedNode.attrs.alt || '';
          img.title = updatedNode.attrs.title || '';
          img.className = updatedNode.attrs.class || 'max-w-full h-auto rounded-lg';

          // Apply alignment styles to container
          applyContainerStyles(updatedNode.attrs);

          // Update image display style based on alignment
          const style = updatedNode.attrs.style || '';
          const hasExplicitSize = style.match(/width:\s*\d+px[^;]*;?\s*height:\s*\d+px[^;]*;?/);

          // Handle all alignment types with explicit size logic
          if (style.includes('float: left')) {
            if (hasExplicitSize) {
              container.classList.add('has-explicit-size');
            } else {
              container.classList.remove('has-explicit-size');
            }
          } else if (style.includes('float: right')) {
            if (hasExplicitSize) {
              container.classList.add('has-explicit-size');
            } else {
              container.classList.remove('has-explicit-size');
            }
          } else if ((style.includes('float: none') && style.includes('display: block') && style.includes('margin:') && style.includes('auto')) ||
                     (style.includes('max-width: 100%') && style.includes('float: none')) ||
                     (style.includes('max-width: 80%') && style.includes('float: none'))) {
            // For center alignment, manage container classes for CSS targeting
            if (hasExplicitSize) {
              container.classList.add('has-explicit-size');
            } else {
              container.classList.remove('has-explicit-size');
            }

            // Image should be block for proper centering with margin: auto
            img.style.setProperty('display', 'block', 'important');
            img.style.setProperty('margin', '0 auto', 'important');
          } else {
            // For other alignments, keep as block and remove center-specific classes
            img.style.setProperty('display', 'block', 'important');
            img.style.removeProperty('margin');
            container.classList.remove('has-explicit-size');
          }          // Apply all styles from node attributes to preserve dimensions
          if (updatedNode.attrs.style && !isResizing) {
            // Extract and apply individual style properties
            const styleString = updatedNode.attrs.style;
            const styleProps = styleString.split(';').filter(prop => prop.trim());

            // Store original dimensions if they exist
            let hasWidth = false, hasHeight = false;

            styleProps.forEach(prop => {
              const [property, value] = prop.split(':').map(s => s.trim());
              if (property && value) {
                if (property === 'width') {
                  img.style.setProperty(property, value, 'important'); // Force explicit width
                  hasWidth = true;
                } else if (property === 'height') {
                  img.style.setProperty(property, value, 'important'); // Force explicit height
                  hasHeight = true;
                }
              }
            });

            // If dimensions are set, mark as explicitly sized for CSS targeting
            if (hasWidth && hasHeight) {
              container.classList.add('has-explicit-size');
            }

            // Always ensure user-select is none
            img.style.userSelect = 'none';
          }

          // Apply CSS alignment classes based on the image's class attribute
          const imageClass = updatedNode.attrs.class || '';
          container.className = 'interactive-image-container';
          if (imageClass.includes('image-left')) {
            container.classList.add('image-left');
          } else if (imageClass.includes('image-right')) {
            container.classList.add('image-right');
          } else if (imageClass.includes('image-center')) {
            container.classList.add('image-center');
          } else if (imageClass.includes('image-full')) {
            container.classList.add('image-full');
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

const RichTextEditor = forwardRef(({
  content = '',
  onChange,
  placeholder = 'Start typing...',
  maxLength = 50000, // Default 50k for articles, can be overridden
  className = '',
  height = 'h-32',
  minHeight = '80px',
  maxHeight = '300px',
  mode = 'full', // 'full' or 'inline'
  showToolbar = true,
  editable = true,
  enableAdvancedFeatures = true,
  onImageUpload,
  onVideoUpload,
  onAudioUpload,
  onMediaAttachmentsChange // New prop to get media attachments
}, ref) => {
  // State for dropdown menus
  const [tableDropdownOpen, setTableDropdownOpen] = useState(false);
  const [imageDropdownOpen, setImageDropdownOpen] = useState(false);
  const [rowSubmenuOpen, setRowSubmenuOpen] = useState(false);
  const [columnSubmenuOpen, setColumnSubmenuOpen] = useState(false);

  // State for media attachments with position tracking
  const [mediaAttachments, setMediaAttachments] = useState([]);
  const [isDragging, setIsDragging] = useState(false);

  // Emoji picker state
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [activeEmojiTab, setActiveEmojiTab] = useState('Recent');
  const [recentEmojis, setRecentEmojis] = useState([]);
  const [focusedEmojiIndex, setFocusedEmojiIndex] = useState(0);
  const [emojiTabOffset, setEmojiTabOffset] = useState(0);
  const [searchEmoji, setSearchEmoji] = useState('');
  const [perRow, setPerRow] = useState(10);
  const emojiPickerRef = useRef(null);

  // Mention autocomplete state
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionSuggestions, setMentionSuggestions] = useState([]);
  const [showMentionDropdown, setShowMentionDropdown] = useState(false);
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  const [mentionDropdownPosition, setMentionDropdownPosition] = useState({ top: 0, left: 0 });
  const mentionDropdownRef = useRef(null);
  const mentionCommandRef = useRef(null); // Store the command function

  // Hashtag autocomplete state
  const [hashtagQuery, setHashtagQuery] = useState('');
  const [hashtagSuggestions, setHashtagSuggestions] = useState([]);
  const [showHashtagDropdown, setShowHashtagDropdown] = useState(false);
  const [selectedHashtagIndex, setSelectedHashtagIndex] = useState(0);
  const [hashtagDropdownPosition, setHashtagDropdownPosition] = useState({ top: 0, left: 0 });
  const hashtagDropdownRef = useRef(null);
  const hashtagCommandRef = useRef(null); // Store the command function

  // Emoji categories and custom names
  const CUSTOM_EMOJI_NAMES = {
    '😀':'grinning face','😃':'smiling face','😄':'smiling face open eyes','😁':'beaming face','😆':'grinning squinting','😅':'grinning sweat','😂':'face tears of joy','🤣':'rolling on floor laughing','😊':'smiling blushing','🙂':'slightly smiling','😉':'winking face','😍':'smiling face hearts','🥰':'smiling face hearts','😘':'face blowing kiss','😗':'kissing face','😙':'kissing smiling eyes','😚':'kissing closed eyes','😋':'face savoring food','😜':'winking tongue','🤪':'zany face','😝':'squinting tongue','😛':'face with tongue','🤔':'thinking face','🤗':'hugging face','🤭':'face with hand over mouth','🤫':'shushing face','🤐':'zipper mouth','😐':'neutral face','😑':'expressionless','😶':'no mouth','🙄':'face with rolling eyes','😴':'sleeping face','🤤':'drooling face','😪':'sleepy face','🥱':'yawning face','😳':'flushed face','🥵':'hot face','🥶':'cold face','😱':'screaming in fear','😨':'fearful face','😰':'anxious sweat','😥':'sad but relieved','😢':'crying face','😭':'loudly crying','😤':'face with steam','😠':'angry face','😡':'pouting face','🤬':'cursing face','🤯':'exploding head','🥺':'pleading face','👍':'thumbs up','👎':'thumbs down','👊':'oncoming fist','✊':'raised fist','🤞':'crossed fingers','✌️':'victory hand','🤟':'love-you gesture','🤘':'sign of the horns','👌':'OK hand','🤌':'pinched fingers','🤏':'pinching hand','✋':'raised hand','🖐️':'hand with fingers splayed','🤚':'raised back of hand','🖖':'vulcan salute','👋':'waving hand','👏':'clapping hands','🙌':'raising hands','🤝':'handshake','🙏':'folded hands','❤️':'red heart','💔':'broken heart','💕':'two hearts','💞':'revolving hearts','💖':'sparkling heart','💘':'heart with arrow','💝':'heart with ribbon','💟':'heart decoration','✔️':'check mark','❌':'cross mark','✅':'check mark button','❎':'cross mark button','➕':'heavy plus','➖':'heavy minus','➗':'heavy division'
  };

  const RAW_EMOJI_CATEGORIES = [
    { label: 'Émoticônes', list: '😀 😃 😄 😁 😆 😅 😂 🤣 😊 🙂 🙃 😉 😌 😍 🥰 😘 😗 😙 😚 😋 😜 🤪 😝 😛 🤑 🤗 🤭 🤫 🤔 🤐 🤨 😐 😑 😶 😏 😒 🙄 😬 🤥 😴 🤤 😪 😮‍💨 😌 😔 😪 😮 😯 😲 🥱 😳 🥵 🥶 😱 😨 😰 😥 😢 😭 😤 😠 😡 🤬 🤯 😳 🥺 😟 😦 😧 😮 😬 😑 😯 😲 ☹️ 🙁 😕' },
    { label: 'Gestes', list: '👍 👎 👊 ✊ 🤛 🤜 🤞 ✌️ 🤟 🤘 👌 🤌 🤏 🫰 ✋ 🖐️ 🤚 🖖 👋 🤙 👏 🙌 👐 🤲 🤝 🙏' },
    { label: 'Personnes', list: '👶 👧 🧒 👦 👩 🧑 👨 👩‍🦱 👨‍🦱 👩‍🦰 👨‍🦰 👱‍♀️ 👱 👨‍🦳 👩‍🦳 👨‍🦲 👩‍🦲 🧔 🤴 👸 👳‍♂️ 👳‍♀️ 🧕 👮‍♂️ 👮‍♀️ 🕵️‍♂️ 🕵️‍♀️ 👩‍⚕️ 👨‍⚕️ 👩‍🎓 👨‍🎓 👩‍🏫 👨‍🏫 👩‍💻 👨‍💻 👩‍💼 👨‍💼 👩‍🔧 👨‍🔧 👩‍🔬 👨‍🔬 👩‍🎤 👨‍🎤 👩‍🚀 👨‍🚀 👩‍✈️ 👨‍✈️ 👩‍🚒 👨‍🚒 👩‍🌾 👨‍🌾' },
    { label: 'Animaux', list: '🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐽 🐸 🐵 🙈 🙉 🙊 🐔 🐧 🐦 🐤 🐣 🐥 🦆 🦅 🦉 🦇 🐺 🐗 🐴 🦄 🐝 🐛 🦋 🐌 🐞 🐜 🦂 🕷️ 🐢 🐍 🦎 🐙 🐚 🦑 🦀 🐡 🐠 🐟 🐬 🐳 🐋 🦈 🐊' },
    { label: 'Nourriture', list: '🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🥦 🥬 🥒 🌶️ 🌽 🥕 🧄 🧅 🥔 🍠 🥐 🥯 🍞 🧀 🍗 🍖 🥩 🥓 🍔 🍟 🍕 🌭 🥪 🌮 🌯 🫔 🥙 🧆 🍜 🍝 🍲 🍛 🍣 🍱 🥗' },
    { label: 'Activités', list: '⚽ 🏀 🏈 ⚾ 🎾 🏐 🏉 🎱 🥏 🏓 🏸 🥅 🥊 🥋 🥇 🥈 🥉 🏆 🎮 🕹️ 🎲 ♟️ 🧩 🎯 🎳 🎰' },
    { label: 'Voyages', list: '🚗 🚕 🚙 🚌 🚎 🏎️ 🚓 🚑 🚒 🚐 🛻 🚚 🚛 🚜 🛵 🏍️ 🚲 🛴 ✈️ 🛫 🛬 🚀 🛸 🚁 🚂 🚆 🚇 🚊 🚉 ⛵ 🚤 🚢 ⚓ 🗺️ 🗽 🗼 🏰 🏯 🏟️ 🎡 🎢 🎠 ⛲ ⛱️ 🏖️ 🏝️ 🌋 🗻 🏔️ ⛰️' },
    { label: 'Objets', list: '⌚ 📱 💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 💽 💾 💿 📀 📼 📷 📸 📹 🎥 📞 ☎️ 📠 📺 📻 🎙️ 🎚️ 🎛️ ⏱️ ⏲️ ⏰ 🕰️ 🔋 🔌 💡 🔦 🕯️ 🧯 🛢️ 💸 💵 💴 💶 💷 💰 💳 🧾 💎 📜 📃 📄 📑 📊 📈 📉 🗂️ 📁 📂 🗃️ 🗄️ 🗑️' },
    { label: 'Symboles', list: '❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 ❤️‍🔥 ❤️‍🩹 💔 ❣️ 💕 💞 💓 💗 💖 💘 💝 💟 ☮️ ✝️ ☪️ 🕉️ ☸️ ✡️ 🔯 🕎 ☯️ ☦️ ☢️ ☣️ ♻️ ⚜️ 🔱 📛 🔰 ⭕ ✅ ☑️ ✔️ ❌ ❎ ➕ ➖ ➗ ➰ ➿ ✳️ ✴️ ❇️ ©️ ®️ ™️' }
  ];

  const EMOJI_CATEGORIES = RAW_EMOJI_CATEGORIES.map(cat => {
    const chars = cat.list.split(/\s+/).filter(Boolean);
    return {
      label: cat.label,
      items: chars.map((ch, idx) => ({
        char: ch,
        name: CUSTOM_EMOJI_NAMES[ch] || `${cat.label.toLowerCase()} ${idx+1}`
      }))
    };
  });

  // Load recent emojis from localStorage
  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('richtexteditor_recent_emojis') || '[]');
      if (Array.isArray(stored)) setRecentEmojis(stored);
    } catch(_) {}
  }, []);

  // Persist recent emojis when changed
  useEffect(() => {
    try {
      localStorage.setItem('richtexteditor_recent_emojis', JSON.stringify(recentEmojis.slice(0, 60)));
    } catch(_) {}
  }, [recentEmojis]);

  // Search for mentionable users when mention query changes
  useEffect(() => {
    const searchMentions = async () => {
      if (!mentionQuery || mentionQuery.length < 1) {
        setMentionSuggestions([]);
        return;
      }

      try {
        const results = await socialAPI.searchMentionableUsers(mentionQuery);
        setMentionSuggestions(results || []);
      } catch (error) {        setMentionSuggestions([]);
      }
    };

    const debounceTimer = setTimeout(searchMentions, 300);
    return () => clearTimeout(debounceTimer);
  }, [mentionQuery]);

  // Search for hashtags when hashtag query changes
  useEffect(() => {
    const searchHashtags = async () => {
      if (!hashtagQuery || hashtagQuery.length < 1) {
        setHashtagSuggestions([]);
        return;
      }

      try {
        const results = await socialAPI.searchHashtags(hashtagQuery, 20);
        setHashtagSuggestions(results || []);
      } catch (error) {        setHashtagSuggestions([]);
      }
    };

    const debounceTimer = setTimeout(searchHashtags, 300);
    return () => clearTimeout(debounceTimer);
  }, [hashtagQuery]);

  const pushRecentEmoji = (emoji) => {
    setRecentEmojis(prev => {
      const filtered = prev.filter(e => e !== emoji);
      return [emoji, ...filtered].slice(0, 60);
    });
  };

  const insertEmoji = (emoji) => {
    if (editor) {
      editor.chain().focus().insertContent(emoji + ' ').run();
      pushRecentEmoji(emoji.trim());
    }
  };

  // Emoji picker functions
  const EMOJI_TABS = ['Recent', ...EMOJI_CATEGORIES.map(c => c.label)];

  const ensureTabVisible = (tab) => {
    const idx = EMOJI_TABS.indexOf(tab);
    if (idx === -1) return;
    if (idx < emojiTabOffset) setEmojiTabOffset(idx);
    else if (idx >= emojiTabOffset + 4) setEmojiTabOffset(Math.min(idx - 3, EMOJI_TABS.length - 4));
  };

  useEffect(() => {
    ensureTabVisible(activeEmojiTab);
  }, [activeEmojiTab]);

  // Handle outside clicks to close emoji picker
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showEmojiPicker && emojiPickerRef.current && !emojiPickerRef.current.contains(event.target)) {
        setShowEmojiPicker(false);
      }
      if (showMentionDropdown && mentionDropdownRef.current && !mentionDropdownRef.current.contains(event.target)) {
        setShowMentionDropdown(false);
      }
      if (showHashtagDropdown && hashtagDropdownRef.current && !hashtagDropdownRef.current.contains(event.target)) {
        setShowHashtagDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showEmojiPicker, showMentionDropdown, showHashtagDropdown]);

  const visibleTabs = EMOJI_TABS.slice(emojiTabOffset, emojiTabOffset + 4);
  const baseEmojiSet = activeEmojiTab === 'Recent'
    ? recentEmojis.map((ch, i) => ({ char: ch, name: CUSTOM_EMOJI_NAMES[ch] || `recent ${i+1}` }))
    : (EMOJI_CATEGORIES.find(c => c.label === activeEmojiTab)?.items || []);
  const lowerSearch = searchEmoji.trim().toLowerCase();
  const currentEmojiSet = baseEmojiSet.filter(e => !lowerSearch || e.char.includes(lowerSearch) || e.name.toLowerCase().includes(lowerSearch));

  const handleTabPrev = () => setEmojiTabOffset(o => Math.max(0, o - 1));
  const handleTabNext = () => setEmojiTabOffset(o => Math.min(EMOJI_TABS.length - 4, o + 1));

  const handleEmojiKeyDown = (e) => {
    if (!showEmojiPicker) return;
    const total = currentEmojiSet.length;
    const ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) {
      e.preventDefault();
      const tabs = EMOJI_TABS;
      let idx = tabs.indexOf(activeEmojiTab);
      if (e.key === 'ArrowRight') idx = (idx + 1) % tabs.length;
      else idx = (idx - 1 + tabs.length) % tabs.length;
      const nextTab = tabs[idx];
      setActiveEmojiTab(nextTab);
      setTimeout(() => ensureTabVisible(nextTab), 0);
      return;
    }
    if (!total) return;
    let next = focusedEmojiIndex;
    if (e.key === 'ArrowRight') { e.preventDefault(); next = Math.min(focusedEmojiIndex + 1, total - 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); next = Math.max(focusedEmojiIndex - 1, 0); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); next = Math.min(focusedEmojiIndex + perRow, total - 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); next = Math.max(focusedEmojiIndex - perRow, 0); }
    else if (e.key === 'Home') { e.preventDefault(); next = 0; }
    else if (e.key === 'End') { e.preventDefault(); next = total - 1; }
    else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); const emo = currentEmojiSet[focusedEmojiIndex]; if (emo) insertEmoji(emo.char + ' '); return; }
    else if (e.key === 'Escape') { e.preventDefault(); setShowEmojiPicker(false); return; }
    if (next !== focusedEmojiIndex) {
      setFocusedEmojiIndex(next);
      const btn = emojiPickerRef.current?.querySelector(`[data-emoji-index="${next}"]`);
      btn && btn.focus();
    }
  };

  // Recompute items per row after render when picker/tab changes
  useEffect(() => {
    if (!showEmojiPicker) return;
    const picker = emojiPickerRef.current;
    if (!picker) return;
    requestAnimationFrame(() => {
      const buttons = picker.querySelectorAll('[data-emoji-index]');
      if (!buttons.length) return;
      const top0 = buttons[0].offsetTop;
      let count = 0;
      for (let i = 0; i < buttons.length; i++) {
        if (buttons[i].offsetTop !== top0) break;
        count++;
      }
      if (count > 0) setPerRow(count);
      setFocusedEmojiIndex(0);
      setTimeout(() => {
        const first = picker.querySelector('[data-emoji-index="0"]');
        first && first.focus();
      }, 30);
    });
  }, [showEmojiPicker, activeEmojiTab]);

  // Memoize extensions to prevent recreation on every render
  const extensions = useMemo(() => {
    // Base extensions for all modes
    const baseExtensions = [
      StarterKit.configure({
        heading: mode === 'inline' ? false : {
          levels: [1, 2, 3, 4, 5, 6]
        },
        // Disable some extensions to use our enhanced versions
        link: false,
        codeBlock: mode === 'inline' ? false : false,
        horizontalRule: mode === 'inline' ? false : false,
        underline: false,
        image: mode === 'inline' ? false : false,
        // Configure history with enhanced settings
        history: {
          depth: 100,
          newGroupDelay: 500,
        },
        // Basic text formatting
        bold: true,
        italic: true,
        strike: mode === 'inline' ? false : true,
        code: mode === 'inline' ? false : true,
        paragraph: true,
        text: true,
        document: true,
        gapcursor: true,
        hardBreak: true,
        listItem: mode === 'inline' ? false : true,
        orderedList: mode === 'inline' ? false : true,
        bulletList: mode === 'inline' ? false : true,
        blockquote: mode === 'inline' ? false : true,
      }),
      Placeholder.configure({
        placeholder: placeholder,
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 hover:text-blue-800 underline',
        },
      }),
      CharacterCount.configure({
        limit: maxLength,
      }),
      TextStyle,
      Underline,
    ];

    // Add full-mode-only extensions
    if (mode === 'full' && enableAdvancedFeatures) {
      return [
        ...baseExtensions,
        Color.configure({
          types: ['textStyle'],
        }),
        Highlight.configure({
          multicolor: true,
        }),
        TextAlign.configure({
          types: ['heading', 'paragraph'],
        }),
        Subscript,
        Superscript,
        Table.configure({
          resizable: true,
        }),
        TableRow,
        TableHeader,
        TableCell,
        TaskList,
        TaskItem.configure({
          nested: true,
        }),
        InteractiveImageResize,
        InteractiveAudioResize,
        InteractiveVideoResize,
        CodeBlock.configure({
          HTMLAttributes: {
            class: 'bg-gray-100 rounded-lg p-4 my-2',
          },
        }),
        HorizontalRule,
        Typography,
        Focus.configure({
          className: 'has-focus',
          mode: 'all',
        }),
        Dropcursor,
        Mention.configure({
          HTMLAttributes: {
            class: 'mention text-blue-600 font-medium',
          },
          suggestion: {
            char: '@',
            allowSpaces: false,
            items: ({ query }) => {
              // Trigger mention search
              setMentionQuery(query);
              setShowMentionDropdown(query.length > 0);
              return mentionSuggestions;
            },
            render: () => {
              return {
                onStart: (props) => {
                  // Store the command function so onClick can use it
                mentionCommandRef.current = props.command;

                if (!props.clientRect) return;

                // Get the cursor position relative to viewport
                const rect = props.clientRect();
                if (rect) {
                  // Position dropdown just below the cursor, accounting for scroll
                  setMentionDropdownPosition({
                    top: rect.bottom + 5, // Add 5px gap below cursor
                    left: rect.left,
                  });
                }
                setShowMentionDropdown(true);
                setSelectedMentionIndex(0);
              },
              onUpdate: (props) => {
                // Update the command function reference
                mentionCommandRef.current = props.command;

                if (!props.clientRect) return;

                const rect = props.clientRect();
                if (rect) {
                  setMentionDropdownPosition({
                    top: rect.bottom + 5,
                    left: rect.left,
                  });
                }
                setSelectedMentionIndex(0);
              },
              onKeyDown: (props) => {
                if (props.event.key === 'ArrowUp') {
                  setSelectedMentionIndex((prev) => Math.max(0, prev - 1));
                  return true;
                }
                if (props.event.key === 'ArrowDown') {
                  setSelectedMentionIndex((prev) =>
                    Math.min(mentionSuggestions.length - 1, prev + 1)
                  );
                  return true;
                }
                if (props.event.key === 'Enter') {
                  if (mentionSuggestions[selectedMentionIndex]) {
                    // Use the command function from props to properly replace
                    props.command({
                      id: mentionSuggestions[selectedMentionIndex].id,
                      label: mentionSuggestions[selectedMentionIndex].username,
                    });
                  }
                  return true;
                }
                if (props.event.key === 'Escape') {
                  setShowMentionDropdown(false);
                  return true;
                }
                return false;
              },
              onExit: () => {
                setShowMentionDropdown(false);
                setMentionQuery('');
                setMentionSuggestions([]);
              },
            };
          },
        },
      }),
      Mention.extend({
        name: 'hashtag',
      }).configure({
        HTMLAttributes: {
          class: 'hashtag text-blue-600 font-medium',
        },
        suggestion: {
          char: '#',
          allowSpaces: false,
          items: ({ query }) => {
            // Trigger hashtag search
            setHashtagQuery(query);
            setShowHashtagDropdown(query.length > 0);
            return hashtagSuggestions;
          },
          render: () => {
            return {
              onStart: (props) => {
                // Store the command function so onClick can use it
                hashtagCommandRef.current = props.command;

                if (!props.clientRect) return;

                // Get the cursor position relative to viewport
                const rect = props.clientRect();
                if (rect) {
                  // Position dropdown just below the cursor, accounting for scroll
                  setHashtagDropdownPosition({
                    top: rect.bottom + 5, // Add 5px gap below cursor
                    left: rect.left,
                  });
                }
                setShowHashtagDropdown(true);
                setSelectedHashtagIndex(0);
              },
              onUpdate: (props) => {
                // Update the command function reference
                hashtagCommandRef.current = props.command;

                if (!props.clientRect) return;

                const rect = props.clientRect();
                if (rect) {
                  setHashtagDropdownPosition({
                    top: rect.bottom + 5,
                    left: rect.left,
                  });
                }
                setSelectedHashtagIndex(0);
              },
              onKeyDown: (props) => {
                if (props.event.key === 'ArrowUp') {
                  setSelectedHashtagIndex((prev) => Math.max(0, prev - 1));
                  return true;
                }
                if (props.event.key === 'ArrowDown') {
                  setSelectedHashtagIndex((prev) =>
                    Math.min(hashtagSuggestions.length - 1, prev + 1)
                  );
                  return true;
                }
                if (props.event.key === 'Enter') {
                  if (hashtagSuggestions[selectedHashtagIndex]) {
                    // Use the command function from props to properly replace
                    props.command({
                      id: hashtagSuggestions[selectedHashtagIndex].name,
                      label: hashtagSuggestions[selectedHashtagIndex].name,
                    });
                  }
                  return true;
                }
                if (props.event.key === 'Escape') {
                  setShowHashtagDropdown(false);
                  return true;
                }
                return false;
              },
              onExit: () => {
                setShowHashtagDropdown(false);
                setHashtagQuery('');
                setHashtagSuggestions([]);
              },
            };
          },
        },
      }),
      ];
    }

    // Return base extensions for inline mode
    return baseExtensions;
  }, [
    mode,
    placeholder,
    maxLength,
    enableAdvancedFeatures,
    mentionSuggestions,
    selectedMentionIndex,
    hashtagSuggestions,
    selectedHashtagIndex,
  ]);

  const editor = useEditor({
    extensions,
    content: content,
    editable: editable,
    onUpdate: ({ editor }) => {
      const content = editor.getHTML();
      const attachmentsWithPositions = getMediaAttachmentsWithPositions();
      onChange && onChange(content, attachmentsWithPositions);
      onMediaAttachmentsChange && onMediaAttachmentsChange(attachmentsWithPositions);
    },
    editorProps: {
      attributes: {
        class: `focus:outline-none p-3 ${
          mode === 'inline'
            ? 'overflow-y-auto rich-text-content'
            : `${height} overflow-y-auto rich-text-content`
        }`,
        style: mode === 'inline' ? `min-height: ${minHeight}; max-height: ${maxHeight};` : '',
      },
      handleDrop: (view, event, slice, moved) => {
        // Note: Image repositioning is now handled by smooth drag system
        // Only handle external file drops here
        return false; // Let other handlers process the drop
      },
      handleDragOver: (view, event) => {
        // Allow dropping
        event.preventDefault();
        return false;
      }
    },
  });

  const setLink = useCallback(() => {
    if (!editor) return;

    const previousUrl = editor.getAttributes('link').href;
    const url = window.prompt('URL', previousUrl);

    // cancelled
    if (url === null) {
      return;
    }

    // empty
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }

    // update link
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
  }, [editor]);

  const unsetLink = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().unsetLink().run();
  }, [editor]);

  const addImage = useCallback(() => {
    if (!editor) return;
    const url = window.prompt('Image URL');
    if (url) {
      editor.chain().focus().insertContent(`<img src="${url}" alt="" class="max-w-full h-auto rounded-lg" />`).run();
    }
  }, [editor]);

  // Image alignment functions
  // Helper function to generate alignment attributes (ensures preview matches actual save)
  const generateAlignmentAttributes = useCallback((imageNode, alignment, isPreview = false) => {
    const attrs = { ...imageNode.attrs };

    // Extract existing dimensions first to check if explicit width exists
    const currentSize = attrs.style || '';
    const widthMatch = currentSize.match(/width:\s*([^;]+);?/);
    const heightMatch = currentSize.match(/height:\s*([^;]+);?/);
    const hasExplicitDimensions = widthMatch !== null || heightMatch !== null;

    // Set class with has-explicit-size if dimensions exist
    let classNames = `max-w-full h-auto rounded-lg image-${alignment}`;
    if (hasExplicitDimensions) {
      classNames += ' has-explicit-size';
    }
    attrs.class = classNames;

    // Add specific styles based on alignment
    let alignmentStyle = '';

    if (alignment === 'left') {
      if (isPreview) {
        // Preview: use margin-based positioning
        alignmentStyle = 'display: block; margin: 0.75rem auto 0.75rem 0; box-sizing: border-box;';
      } else {
        // Content: use block display for consistency with center alignment
        alignmentStyle = 'display: block; margin: 0.75rem auto 0.75rem 0; box-sizing: border-box;';
      }
    } else if (alignment === 'right') {
      if (isPreview) {
        // Preview: use margin-based positioning
        alignmentStyle = 'display: block; margin: 0.75rem 0 0.75rem auto; box-sizing: border-box;';
      } else {
        // Content: use block display for consistency with center alignment
        alignmentStyle = 'display: block; margin: 0.75rem 0 0.75rem auto; box-sizing: border-box;';
      }
    } else if (alignment === 'center') {
      alignmentStyle = 'display: block; margin: 0.5rem auto;';
    } else if (alignment === 'full') {
      alignmentStyle = 'display: block; width: 100% !important; max-width: 100%; margin: 1rem 0;';
    }

    // Preserve existing size styles with !important flags to ensure they're not overridden
    let sizeStyle = '';
    if (widthMatch && heightMatch) {
      sizeStyle = `width: ${widthMatch[1]}; height: ${heightMatch[1]};`;
    } else if (widthMatch) {
      sizeStyle = `width: ${widthMatch[1]};`;
    } else if (heightMatch) {
      sizeStyle = `height: ${heightMatch[1]};`;
    }

    // For preview mode, remove any display properties from size styles to avoid conflicts
    if (isPreview) {
      sizeStyle = sizeStyle.replace(/display:\s*[^;!]+(!important)?;?\s*/gi, '');
    }

    // Ensure alignment styles come LAST so display property takes precedence
    attrs.style = (sizeStyle + ' ' + alignmentStyle).trim();

    return attrs;
  }, []);

  const setImageAlignment = useCallback((alignment) => {
    if (!editor) return;

    const { state } = editor;
    const { selection } = state;
    const { from, to } = selection;

    // Find image nodes in the current selection or around cursor
    let imageNode = null;
    let imagePos = null;

    // Check if we have selected an image
    if (selection.node && selection.node.type.name === 'interactiveImage') {
      imageNode = selection.node;
      imagePos = from;
    } else {
      // Look for images around the cursor
      state.doc.nodesBetween(Math.max(0, from - 1), Math.min(state.doc.content.size, to + 1), (node, pos) => {
        if (node.type.name === 'interactiveImage' && !imageNode) {
          imageNode = node;
          imagePos = pos;
        }
      });

      // If still no image found, look for any image in the document (fallback)
      if (!imageNode) {
        state.doc.descendants((node, pos) => {
          if (node.type.name === 'interactiveImage' && !imageNode) {
            imageNode = node;
            imagePos = pos;
            return false; // Stop searching after finding first image
          }
        });
      }
    }

    if (imageNode && imagePos !== null) {
      // Use the shared alignment logic
      const attrs = generateAlignmentAttributes(imageNode, alignment);

      editor.view.dispatch(
        editor.state.tr.setNodeMarkup(imagePos, undefined, attrs)
      );
    }
  }, [editor, generateAlignmentAttributes]);

  const previewImageAlignment = useCallback((alignment) => {
    if (!editor) return;

    const { state } = editor;
    const { selection } = state;
    const { from, to } = selection;

    // Find image nodes in the current selection or around cursor
    let imageNode = null;
    let imagePos = null;

    // Check if we have selected an image
    if (selection.node && selection.node.type.name === 'interactiveImage') {
      imageNode = selection.node;
      imagePos = from;
    } else {
      // Look for images around the cursor
      state.doc.nodesBetween(Math.max(0, from - 1), Math.min(state.doc.content.size, to + 1), (node, pos) => {
        if (node.type.name === 'interactiveImage' && !imageNode) {
          imageNode = node;
          imagePos = pos;
        }
      });

      // If still no image found, look for any image in the document (fallback)
      if (!imageNode) {
        state.doc.descendants((node, pos) => {
          if (node.type.name === 'interactiveImage' && !imageNode) {
            imageNode = node;
            imagePos = pos;
            return false; // Stop searching after finding first image
          }
        });
      }
    }

    if (imageNode && imagePos !== null) {
      // Store original attributes before preview
      const originalAttrs = { ...imageNode.attrs };

      // Generate preview attributes using the same logic as setImageAlignment
      const previewAttrs = generateAlignmentAttributes(imageNode, alignment, true);

      // Apply the preview by temporarily updating the node
      const tempTransaction = editor.state.tr.setNodeMarkup(imagePos, undefined, previewAttrs);
      editor.view.dispatch(tempTransaction);

      // Add visual preview indicator after a brief delay to allow DOM update
      setTimeout(() => {
        const containerElement = editor.view.nodeDOM(imagePos)?.querySelector('.interactive-image-container');
        if (containerElement) {
          containerElement.style.transition = 'all 0.2s ease';
          containerElement.style.opacity = '0.8';
          containerElement.style.outline = '2px solid #3b82f6';
          containerElement.style.outlineOffset = '2px';

          // Store the preview state so we can revert it
          containerElement.dataset.isPreviewing = 'true';
          containerElement.dataset.originalAttrs = JSON.stringify(originalAttrs);
        }
      }, 10);
    }
  }, [editor, generateAlignmentAttributes]);  const clearImagePreview = useCallback(() => {
    if (!editor) return;

    // Find all previewing images and revert them to their original state
    const imageContainers = editor.view.dom.querySelectorAll('.interactive-image-container[data-is-previewing="true"]');

    imageContainers.forEach(container => {
      const originalAttrs = container.dataset.originalAttrs;
      if (originalAttrs) {
        try {
          const attrs = JSON.parse(originalAttrs);

          // Find the position of this container in the document
          const allContainers = Array.from(editor.view.dom.querySelectorAll('.interactive-image-container'));
          const containerIndex = allContainers.indexOf(container);

          // Find the corresponding node in the document
          let nodePos = null;
          let currentIndex = 0;

          editor.state.doc.descendants((node, pos) => {
            if (node.type.name === 'interactiveImage') {
              if (currentIndex === containerIndex) {
                nodePos = pos;
                return false; // Stop searching
              }
              currentIndex++;
            }
          });

          if (nodePos !== null) {
            // Revert the node to its original attributes
            const revertTransaction = editor.state.tr.setNodeMarkup(nodePos, undefined, attrs);
            editor.view.dispatch(revertTransaction);
          }

          // Clean up preview indicators
          container.removeAttribute('data-is-previewing');
          container.removeAttribute('data-original-attrs');

        } catch (error) {        }
      }
    });

    // Also clean up any remaining visual indicators after a short delay
    setTimeout(() => {
      const remainingContainers = editor.view.dom.querySelectorAll('.interactive-image-container');
      remainingContainers.forEach(container => {
        // Clean up visual indicators
        container.style.transition = '';
        container.style.opacity = '';
        container.style.outline = '';
        container.style.outlineOffset = '';
      });
    }, 50);
  }, [editor]);  const alignImageLeft = useCallback(() => setImageAlignment('left'), [setImageAlignment]);
  const alignImageCenter = useCallback(() => setImageAlignment('center'), [setImageAlignment]);
  const alignImageRight = useCallback(() => setImageAlignment('right'), [setImageAlignment]);
  const alignImageFull = useCallback(() => setImageAlignment('full'), [setImageAlignment]);

  const addTable = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
  }, [editor]);

  const addCodeBlock = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().toggleCodeBlock().run();
  }, [editor]);

  // Table manipulation functions
  const addRowAbove = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().addRowBefore().run();
  }, [editor]);

  const addRowBelow = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().addRowAfter().run();
  }, [editor]);

  const deleteRow = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().deleteRow().run();
  }, [editor]);

  const addColumnLeft = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().addColumnBefore().run();
  }, [editor]);

  const addColumnRight = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().addColumnAfter().run();
  }, [editor]);

  const deleteColumn = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().deleteColumn().run();
  }, [editor]);

  const deleteTable = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().deleteTable().run();
  }, [editor]);

  // Utility functions for file handling (similar to PostComposer)
  const detectType = useCallback((file) => {
    if (ACCEPT_IMAGE.includes(file.type)) return 'image';
    if (ACCEPT_VIDEO.includes(file.type)) return 'video';
    if (ACCEPT_AUDIO.includes(file.type)) return 'audio';
    if (ACCEPT_PDF.includes(file.type)) return 'file';
    return null;
  }, []);

  const checkMediaDuration = useCallback((file) => {
    return new Promise((resolve) => {
      const mediaElement = detectType(file) === 'video'
        ? document.createElement('video')
        : document.createElement('audio');

      const onLoadedMetadata = () => {
        const duration = mediaElement.duration;
        mediaElement.removeEventListener('loadedmetadata', onLoadedMetadata);
        URL.revokeObjectURL(mediaElement.src);
        resolve(duration);
      };

      const onError = () => {
        mediaElement.removeEventListener('error', onError);
        URL.revokeObjectURL(mediaElement.src);
        resolve(null);
      };

      mediaElement.addEventListener('loadedmetadata', onLoadedMetadata);
      mediaElement.addEventListener('error', onError);
      mediaElement.src = URL.createObjectURL(file);
    });
  }, [detectType]);

  const addFiles = useCallback(async (fileList) => {
    if (!editor) return;

    const fileArray = Array.from(fileList);

    for (const f of fileArray) {
      const kind = detectType(f);
      if (!kind) continue;

      // Check duration for video and audio files
      if (kind === 'video' || kind === 'audio') {
        try {
          const duration = await checkMediaDuration(f);
          if (duration && duration > 300) { // 5 minutes = 300 seconds
            const minutes = Math.floor(duration / 60);
            const seconds = Math.floor(duration % 60);
            alert(`${kind === 'video' ? 'Video' : 'Audio'} files must be 5 minutes or less. Current duration: ${minutes}:${seconds.toString().padStart(2, '0')}`);
            continue;
          }
        } catch (error) {        }
      }

      // Insert media placeholder at cursor position
      insertMediaPlaceholder(f, kind);
    }
  }, [editor, detectType, checkMediaDuration]);

  // Insert media placeholder at cursor position
  const insertMediaPlaceholder = useCallback((file, type) => {
    if (!editor) return;

    const mediaId = crypto.randomUUID();
    const preview = URL.createObjectURL(file);

    // Add to media attachments with position tracking
    const newAttachment = {
      id: mediaId,
      file: file,
      type: type,
      preview: preview,
      name: file.name,
      size: file.size
    };

    setMediaAttachments(prev => [...prev, newAttachment]);

    // Insert placeholder in editor content
    if (type === 'image') {
      editor.chain().focus().insertContent(
        `<img src="${preview}" alt="${file.name}" class="max-w-full h-auto rounded-lg" data-media-id="${mediaId}" data-media-type="image" />`
      ).run();
    } else if (type === 'video') {
      editor.chain().focus().insertContent(
        `<div data-media-id="${mediaId}" data-media-type="video" style="border: 2px dashed #3b82f6; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; background-color: #eff6ff; text-align: center;">
          <video src="${preview}" style="max-width: 200px; max-height: 150px; border-radius: 0.25rem; margin-bottom: 0.5rem;" muted></video>
          <div style="font-size: 0.875rem; color: #1d4ed8; font-weight: 500;">🎥 Video: ${file.name}</div>
          <div style="font-size: 0.75rem; color: #6b7280;">${(file.size / 1024 / 1024).toFixed(1)} MB</div>
        </div>`
      ).run();
    } else if (type === 'audio') {
      editor.chain().focus().insertContent(
        `<div data-media-id="${mediaId}" data-media-type="audio" style="border: 2px dashed #3b82f6; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; background-color: #eff6ff; text-align: center;">
          <div style="width: 200px; height: 100px; background-color: #dbeafe; border-radius: 0.25rem; margin: 0 auto 0.5rem; display: flex; align-items: center; justify-content: center; font-size: 2rem;">🎵</div>
          <div style="font-size: 0.875rem; color: #1d4ed8; font-weight: 500;">🎵 Audio: ${file.name}</div>
          <div style="font-size: 0.75rem; color: #6b7280;">${(file.size / 1024 / 1024).toFixed(1)} MB</div>
        </div>`
      ).run();
    } else if (type === 'file') {
      editor.chain().focus().insertContent(
        `<div data-media-id="${mediaId}" data-media-type="file" style="border: 2px dashed #3b82f6; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; background-color: #eff6ff; text-align: center;">
          <div style="width: 200px; height: 100px; background-color: #dbeafe; border-radius: 0.25rem; margin: 0 auto 0.5rem; display: flex; align-items: center; justify-content: center; font-size: 2rem;">📄</div>
          <div style="font-size: 0.875rem; color: #1d4ed8; font-weight: 500;">📄 File: ${file.name}</div>
          <div style="font-size: 0.75rem; color: #6b7280;">${(file.size / 1024 / 1024).toFixed(1)} MB</div>
        </div>`
      ).run();
    }
  }, [editor]);

  // Get media attachments with their positions in content
  const getMediaAttachmentsWithPositions = useCallback(() => {
    if (!editor) return [];

    const content = editor.getHTML();
    const attachmentsWithPositions = [];

    mediaAttachments.forEach(attachment => {
      const regex = new RegExp(`data-media-id="${attachment.id}"`, 'g');
      const match = regex.exec(content);
      if (match) {
        attachmentsWithPositions.push({
          ...attachment,
          position: match.index
        });
      }
    });

    // Sort by position in content
    return attachmentsWithPositions.sort((a, b) => a.position - b.position);
  }, [editor, mediaAttachments]);

  // Remove media attachment
  const removeMediaAttachment = useCallback((mediaId) => {
    setMediaAttachments(prev => prev.filter(att => att.id !== mediaId));

    // Remove from editor content
    if (editor) {
      const content = editor.getHTML();
      const updatedContent = content.replace(
        new RegExp(`<div data-media-id="${mediaId}"[^>]*>.*?</div>`, 's'),
        ''
      );
      editor.commands.setContent(updatedContent);
    }
  }, [editor]);

  // Process content for submission - replace placeholders with uploaded media
  const processContentForSubmission = useCallback(async (uploadHandlers = {}) => {
    if (!editor) return { content: '', mediaFiles: [] };

    let processedContent = editor.getHTML();
    const mediaFiles = [];

    for (const attachment of mediaAttachments) {
      const { id, file, type } = attachment;

      try {
        let mediaUrl = null;

        // Upload media based on type
        if (type === 'image' && uploadHandlers.onImageUpload) {
          mediaUrl = await uploadHandlers.onImageUpload(file);
        } else if (type === 'video' && uploadHandlers.onVideoUpload) {
          mediaUrl = await uploadHandlers.onVideoUpload(file);
        } else if (type === 'audio' && uploadHandlers.onAudioUpload) {
          mediaUrl = await uploadHandlers.onAudioUpload(file);
        }

        if (mediaUrl) {
          // Replace placeholder with actual media element
          if (type === 'image') {
            processedContent = processedContent.replace(
              new RegExp(`<div data-media-id="${id}"[^>]*>.*?</div>`, 's'),
              `<img src="${mediaUrl}" alt="${file.name}" style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 0.5rem 0;" />`
            );
          } else if (type === 'video') {
            processedContent = processedContent.replace(
              new RegExp(`<div data-media-id="${id}"[^>]*>.*?</div>`, 's'),
              `<video controls style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 0.5rem 0;">
                <source src="${mediaUrl}" type="${file.type}">
                Your browser does not support the video tag.
              </video>`
            );
          } else if (type === 'audio') {
            processedContent = processedContent.replace(
              new RegExp(`<div data-media-id="${id}"[^>]*>.*?</div>`, 's'),
              `<audio controls style="max-width: 100%; margin: 0.5rem 0;">
                <source src="${mediaUrl}" type="${file.type}">
                Your browser does not support the audio tag.
              </audio>`
            );
          }

          mediaFiles.push({
            id,
            url: mediaUrl,
            type,
            name: file.name,
            size: file.size
          });
        } else {
          // If upload failed, remove the placeholder
          processedContent = processedContent.replace(
            new RegExp(`<div data-media-id="${id}"[^>]*>.*?</div>`, 's'),
            `<div style="border: 2px solid #ef4444; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; color: #dc2626; background-color: #fef2f2;">
              Failed to upload ${type}: ${file.name}
            </div>`
          );
        }
      } catch (error) {        // Replace with error message
        processedContent = processedContent.replace(
          new RegExp(`<div data-media-id="${id}"[^>]*>.*?</div>`, 's'),
          `<div style="border: 2px solid #ef4444; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; color: #dc2626; background-color: #fef2f2;">
            Error uploading ${type}: ${file.name}
          </div>`
        );
      }
    }

    return {
      content: processedContent,
      mediaFiles: mediaFiles,
      rawMediaAttachments: mediaAttachments
    };
  }, [editor, mediaAttachments]);

  // Note: Component exposes media attachment methods through props
  // getMediaAttachments, getMediaAttachmentsWithPositions, removeMediaAttachment,
  // processContentForSubmission available through onMediaAttachmentsChange prop

  // Drag and drop handlers
  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    setIsDragging(false);

    // Handle file drops from external sources only (internal drag is now handled by smooth drag system)
    if (e.dataTransfer.files?.length) {
      await addFiles(e.dataTransfer.files);
    }
  }, [addFiles]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();

    // Only show upload zone for external file drags
    const hasFiles = e.dataTransfer.types.includes('Files');

    if (hasFiles && !isDragging) {
      setIsDragging(true);
    }
  }, [isDragging]);  const handleDragLeave = useCallback((e) => {
    if (e.relatedTarget == null) setIsDragging(false);
  }, []);

  // Media upload functions - direct insertion system
  const handleImageUpload = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = ACCEPT_IMAGE.join(',');
    input.multiple = true;
    input.onchange = async (e) => {
      if (e.target.files?.length) {
        await addFiles(e.target.files);
      }
    };
    input.click();
  }, [addFiles]);

  const handleVideoUpload = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = ACCEPT_VIDEO.join(',');
    input.multiple = true;
    input.onchange = async (e) => {
      if (e.target.files?.length) {
        await addFiles(e.target.files);
      }
    };
    input.click();
  }, [addFiles]);

  const handleAudioUpload = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = ACCEPT_AUDIO.join(',');
    input.multiple = true;
    input.onchange = async (e) => {
      if (e.target.files?.length) {
        await addFiles(e.target.files);
      }
    };
    input.click();
  }, [addFiles]);

  const handleGenericFileUpload = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = [...ACCEPT_IMAGE, ...ACCEPT_VIDEO, ...ACCEPT_AUDIO, ...ACCEPT_PDF].join(',');
    input.multiple = true;
    input.onchange = async (e) => {
      if (e.target.files?.length) {
        await addFiles(e.target.files);
      }
    };
    input.click();
  }, [addFiles]);

  // Close dropdown when editor loses focus or table is no longer active
  useEffect(() => {
    if (editor && (!editor.isActive('table') || !editor.isFocused)) {
      setTableDropdownOpen(false);
      setRowSubmenuOpen(false);
      setColumnSubmenuOpen(false);
    }

    // Close image dropdown when editor loses focus
    if (editor && !editor.isFocused) {
      setImageDropdownOpen(false);
    }
  }, [editor?.isActive('table'), editor?.isFocused, editor]);

  // Reset submenus when main dropdown closes
  useEffect(() => {
    if (!tableDropdownOpen) {
      setRowSubmenuOpen(false);
      setColumnSubmenuOpen(false);
    }
  }, [tableDropdownOpen]);

  // Expose methods to parent component via ref
  // MUST be called before any conditional returns (React Hooks rules)
  useImperativeHandle(ref, () => ({
    // Get current HTML content
    getHTML: () => editor?.getHTML() || '',

    // Get current JSON content
    getJSON: () => editor?.getJSON() || {},

    // Get current media attachments
    getMediaAttachments: () => mediaAttachments,

    // Process content for submission - upload media and replace placeholders
    processContentForSubmission: async (uploadCallback) => {
      if (!editor) {
        return { processedContent: '', mediaFiles: [] };
      }

      let processedContent = editor.getHTML();
      const mediaFiles = [];

      for (const attachment of mediaAttachments) {
        try {
          // Call upload callback provided by parent
          const mediaUrl = await uploadCallback(attachment.file, attachment.type);

          if (mediaUrl) {
            // Replace placeholder with actual URL based on media type
            if (attachment.type === 'image') {
              // For images: Replace src attribute while preserving other attributes
              const imgRegex = new RegExp(
                `(<img[^>]*data-media-id="${attachment.id}"[^>]*src=")[^"]*("[^>]*>)`,
                'g'
              );
              processedContent = processedContent.replace(imgRegex, `$1${mediaUrl}$2`);

              // Remove data-media-id attribute to clean up
              processedContent = processedContent.replace(
                new RegExp(`\\s*data-media-id="${attachment.id}"`, 'g'),
                ''
              );
            } else if (attachment.type === 'video') {
              // Replace placeholder div with video element
              processedContent = processedContent.replace(
                new RegExp(`<div[^>]*data-media-id="${attachment.id}"[^>]*>.*?</div>`, 's'),
                `<video src="${mediaUrl}" controls class="w-full max-w-2xl rounded-lg"></video>`
              );
            } else if (attachment.type === 'audio') {
              // Replace placeholder div with audio element
              processedContent = processedContent.replace(
                new RegExp(`<div[^>]*data-media-id="${attachment.id}"[^>]*>.*?</div>`, 's'),
                `<audio src="${mediaUrl}" controls class="w-full"></audio>`
              );
            }

            // Add to media files list
            mediaFiles.push({
              type: attachment.type,
              url: mediaUrl,
              file: attachment.file
            });
          }
        } catch (error) {        }
      }

      return { processedContent, mediaFiles };
    },

    // Clear editor content
    clearContent: () => {
      if (editor) {
        editor.commands.clearContent();
        setMediaAttachments([]);
      }
    },

    // Set editor content
    setContent: (newContent) => {
      if (editor) {
        editor.commands.setContent(newContent);
      }
    },

    // Focus editor
    focus: () => {
      if (editor) {
        editor.commands.focus();
      }
    }
  }), [editor, mediaAttachments]);

  if (!editor) {
    return (
      <div className={`border border-gray-300 rounded-md ${height} bg-gray-50 animate-pulse ${className}`} />
    );
  }

  const characterCount = editor.storage.characterCount.characters();
  const isNearLimit = characterCount > maxLength * 0.8;
  const isOverLimit = characterCount > maxLength;

  return (
    <div className={`border border-gray-300 rounded-md focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent bg-white ${className}`}>
      {/* Custom styles for rich text content */}
      <style>{`
        .interactive-image-container {
          position: relative !important;
          display: inline-block !important;
          max-width: 100% !important;
          box-sizing: border-box !important;
          overflow: hidden !important; /* Prevent overflow */
        }

        /* Ensure the interactive container respects preview mode */
        .interactive-image-container:not([data-is-previewing="true"]) {
          display: inline-block !important;
        }

        /* Preview mode overrides for proper alignment */
        .interactive-image-container[data-is-previewing="true"] {
          display: block !important;
        }

        /* More specific preview overrides to ensure they take precedence */
        .rich-text-content .interactive-image-container[data-is-previewing="true"] {
          display: block !important;
          float: none !important;
        }

        /* Additional boundary enforcement */
        .ProseMirror {
          overflow-x: auto !important; /* Allow horizontal scrolling if absolutely needed */
        }

        /* Ensure floating images don't break out of their container */
        .rich-text-content::after {
          content: "" !important;
          display: table !important;
          clear: both !important;
        }

        /* Prevent images from overflowing container boundaries */
        .rich-text-content {
          overflow-wrap: break-word !important;
          word-wrap: break-word !important;
          overflow-x: auto !important; /* Allow horizontal scrolling if needed */
          position: relative !important;
        }

        /* Ensure all image containers respect the preview area boundaries */
        .rich-text-content .interactive-image-container {
          max-width: 100% !important;
          box-sizing: border-box !important;
          overflow: hidden !important; /* Prevent container overflow */
        }

        .rich-text-content .interactive-image-container img {
          max-width: 100% !important;
          height: auto !important;
          box-sizing: border-box !important;
          display: block !important;
        }

        /* Images with explicit dimensions should use their exact size */
        .rich-text-content .interactive-image-container.has-explicit-size img {
          max-width: none !important; /* Remove max-width constraint for explicit sizes */
          width: auto !important; /* Let the inline style take precedence */
          height: auto !important; /* Let the inline style take precedence */
        }

        /* Clear floats after floating images */
        .rich-text-content p:after,
        .rich-text-content div:after {
          content: "";
          display: table;
          clear: both;
        }

        .interactive-image-container:hover .resize-overlay {
          opacity: 1 !important;
        }

        .resize-overlay {
          position: absolute !important;
          top: 0 !important;
          left: 0 !important;
          right: 0 !important;
          bottom: 0 !important;
          border: 2px solid #3b82f6 !important;
          border-radius: 8px !important;
          box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2) !important;
          pointer-events: none !important;
          transition: opacity 0.2s ease !important;
          z-index: 1 !important;
          opacity: 0 !important;
        }

        .resize-handle {
          position: absolute !important;
          width: 12px !important;
          height: 12px !important;
          background: #3b82f6 !important;
          border: 2px solid white !important;
          border-radius: 50% !important;
          pointer-events: auto !important;
          z-index: 10 !important;
          transition: transform 0.1s ease !important;
          cursor: pointer !important;
        }

        .resize-handle:hover {
          transform: scale(1.2) !important;
        }

        .interactive-image-container img {
          user-select: none !important;
          -webkit-user-drag: none !important;
          pointer-events: auto !important;
          display: block !important;
        }

        /* Override any conflicting styles */
        .rich-text-content .interactive-image-container img {
          max-width: none !important;
          max-height: none !important;
          min-width: auto !important;
          min-height: auto !important;
          flex-shrink: 0 !important;
          flex-grow: 0 !important;
          object-fit: contain !important;
        }

        /* Ensure container doesn't constrain the image */
        .interactive-image-container {
          max-width: none !important;
          width: auto !important;
          height: auto !important;
        }

        /* Ensure resize overlay is properly positioned */
        .interactive-image-container .resize-overlay {
          pointer-events: none !important;
        }

        .interactive-image-container .resize-handle {
          pointer-events: auto !important;
        }

        /* Drag handle styles - optimized for smooth dragging */
        .drag-handle {
          position: absolute !important;
          top: 4px !important;
          left: 4px !important;
          width: 24px !important;
          height: 24px !important;
          background: rgba(59, 130, 246, 0.9) !important;
          border-radius: 6px !important;
          cursor: grab !important;
          opacity: 0 !important;
          transition: all 0.2s ease !important;
          z-index: 15 !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          color: white !important;
          font-size: 14px !important;
          font-weight: bold !important;
          user-select: none !important;
          border: 2px solid rgba(255, 255, 255, 0.4) !important;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        }

        .drag-handle:hover {
          background: rgba(59, 130, 246, 1) !important;
          transform: scale(1.1) !important;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
          border-color: rgba(255, 255, 255, 0.6) !important;
        }

        .drag-handle:active {
          cursor: grabbing !important;
          transform: scale(0.95) !important;
          background: rgba(37, 99, 235, 1) !important;
        }

        /* Drop zone indicators */
        .potential-drop-zone.active-drop-zone {
          border-top-color: #3b82f6 !important;
          border-bottom-color: #3b82f6 !important;
          background-color: rgba(59, 130, 246, 0.05) !important;
        }

        /* Ghost image styles for smooth dragging */
        .ghost-drag-image {
          position: fixed !important;
          pointer-events: none !important;
          z-index: 9999 !important;
          border: 2px dashed #3b82f6 !important;
          border-radius: 8px !important;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
          transition: opacity 0.1s ease !important;
          transform-origin: center !important;
        }

        .interactive-image-container:hover .drag-handle {
          opacity: 1 !important;
        }

        .drag-handle:active {
          cursor: grabbing !important;
        }

        /* Drag feedback styles */
        .rich-text-content img[draggable="true"] {
          transition: opacity 0.2s ease !important;
        }

        .rich-text-content .interactive-image-container.dragging {
          opacity: 0.5 !important;
        }

        /* Drop zone indicator */
        .rich-text-content.drag-over {
          background-color: rgba(59, 130, 246, 0.05) !important;
        }

        .rich-text-content p.drop-target {
          background-color: rgba(59, 130, 246, 0.1) !important;
          border: 2px dashed #3b82f6 !important;
          border-radius: 4px !important;
          min-height: 20px !important;
          padding: 4px !important;
        }

        .resize-overlay {
          pointer-events: none !important;
        }

        .resize-handle {
          transition: all 0.2s ease !important;
        }

        .resize-handle:hover {
          background-color: #2563eb !important;
          transform: scale(1.2) !important;
        }

        .interactive-image-container img {
          transition: none !important;
          pointer-events: auto !important;
        }

        .rich-text-content .interactive-image-container img {
          max-width: none !important;
          /* Removed width: auto and height: auto to allow manual sizing */
        }

        .rich-text-content ul {
          list-style-type: disc !important;
          margin-left: 1.5rem !important;
          margin-top: 0.5rem !important;
          margin-bottom: 0.5rem !important;
        }
        .rich-text-content ol {
          list-style-type: decimal !important;
          margin-left: 1.5rem !important;
          margin-top: 0.5rem !important;
          margin-bottom: 0.5rem !important;
        }
        .rich-text-content li {
          margin-bottom: 0.25rem !important;
          display: list-item !important;
        }
        .rich-text-content blockquote {
          border-left: 4px solid #e5e7eb !important;
          padding-left: 1rem !important;
          margin: 1rem 0 !important;
          font-style: italic !important;
          color: #6b7280 !important;
          background-color: #f9fafb !important;
          padding: 0.75rem 1rem !important;
          border-radius: 0.375rem !important;
        }
        .rich-text-content code {
          background-color: #f3f4f6 !important;
          padding: 0.125rem 0.25rem !important;
          border-radius: 0.25rem !important;
          font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace !important;
          font-size: 0.875em !important;
        }
        /* Hashtag styling - client-side detection */
        .rich-text-content .hashtag,
        .rich-text-content a[href^="#"] {
          color: #2563eb !important; /* Blue-600 */
          font-weight: 500 !important;
          cursor: pointer !important;
          text-decoration: none !important;
        }
        .rich-text-content .hashtag:hover,
        .rich-text-content a[href^="#"]:hover {
          color: #1d4ed8 !important; /* Blue-700 */
          text-decoration: underline !important;
        }
        .rich-text-content pre {
          background-color: #f3f4f6 !important;
          padding: 1rem !important;
          border-radius: 0.5rem !important;
          margin: 1rem 0 !important;
          overflow-x: auto !important;
        }
        .rich-text-content p {
          margin-bottom: 0.5rem !important;
        }
        .rich-text-content h1, .rich-text-content h2, .rich-text-content h3,
        .rich-text-content h4, .rich-text-content h5, .rich-text-content h6 {
          font-weight: 600 !important;
          margin-top: 1rem !important;
          margin-bottom: 0.5rem !important;
        }
        .rich-text-content h1 {
          font-size: 2rem !important;
        }
        .rich-text-content h2 {
          font-size: 1.75rem !important;
        }
        .rich-text-content h3 {
          font-size: 1.5rem !important;
        }
        .rich-text-content h4 {
          font-size: 1.25rem !important;
        }
        .rich-text-content h5 {
          font-size: 1.125rem !important;
        }
        .rich-text-content h6 {
          font-size: 1rem !important;
        }
        .rich-text-content strong {
          font-weight: 600 !important;
        }
        .rich-text-content em {
          font-style: italic !important;
        }
        .rich-text-content u {
          text-decoration: underline !important;
        }
        .rich-text-content s {
          text-decoration: line-through !important;
        }
        .rich-text-content sub {
          vertical-align: sub !important;
          font-size: smaller !important;
        }
        .rich-text-content sup {
          vertical-align: super !important;
          font-size: smaller !important;
        }
        .rich-text-content a {
          color: #2563eb !important;
          text-decoration: underline !important;
        }
        .rich-text-content a:hover {
          color: #1d4ed8 !important;
        }
        .rich-text-content mark {
          background-color: #fef08a !important;
          padding: 0.125rem 0.25rem !important;
          border-radius: 0.25rem !important;
        }
        .rich-text-content hr {
          border: none !important;
          border-top: 2px solid #e5e7eb !important;
          margin: 2rem 0 !important;
        }
        .rich-text-content img {
          max-width: 100% !important;
          height: auto !important;
          border-radius: 0.5rem !important;
          margin: 0.5rem 0 !important;
        }
        /* Image Alignment Classes for Inline Images */
        .rich-text-content .interactive-image-container.image-left,
        .rich-text-content .image-left {
          float: left !important;
          margin: 0.75rem 0.75rem 0.75rem 0 !important;
          max-width: 40% !important; /* Increased from min(35%, 200px) */
          box-sizing: border-box !important;
          /* Ensure images respect container boundaries */
          width: auto !important;
          height: auto !important;
          clear: left !important; /* Prevent stacking issues */
        }

        /* Only apply inline-block when NOT in preview mode */
        .rich-text-content .interactive-image-container.image-left:not([data-is-previewing="true"]),
        .rich-text-content .image-left:not([data-is-previewing="true"]) {
          display: inline-block !important;
        }

        /* Preview mode override for left alignment - force block display */
        .rich-text-content .interactive-image-container.image-left[data-is-previewing="true"],
        .rich-text-content .image-left[data-is-previewing="true"] {
          display: block !important;
          float: none !important;
          margin-left: 0 !important;
          margin-right: auto !important;
        }

        /* Even more specific override to ensure preview left alignment works */
        .rich-text-content .interactive-image-container[data-is-previewing="true"].image-left {
          display: block !important;
          float: none !important;
          margin: 0.75rem auto 0.75rem 0 !important;
        }
        /* Override for left images with explicit dimensions - constrain to 60% max to prevent overflow */
        .rich-text-content .interactive-image-container.image-left.has-explicit-size,
        .rich-text-content .image-left.has-explicit-size {
          max-width: 60% !important; /* Prevent boundary overflow while allowing larger sizes */
          /* Don't override explicit width/height */
        }
        .rich-text-content .interactive-image-container.image-center,
        .rich-text-content .image-center {
          display: block !important;
          margin: 0.5rem auto !important;
          text-align: center !important;
          float: none !important;
          max-width: 100% !important; /* Don't over-constrain center images */
          clear: both !important; /* Clear any floats */
        }
        /* For center images, let them use their natural size up to container width */
        .rich-text-content .interactive-image-container.image-center.has-explicit-size,
        .rich-text-content .image-center.has-explicit-size {
          max-width: 100% !important;
          /* Don't override explicit width/height for center images */
        }
        .rich-text-content .interactive-image-container.image-right,
        .rich-text-content .image-right {
          float: right !important;
          margin: 0.75rem 0 0.75rem 0.75rem !important;
          max-width: 40% !important; /* Increased from min(35%, 200px) */
          box-sizing: border-box !important;
          /* Ensure images respect container boundaries */
          width: auto !important;
          height: auto !important;
          clear: right !important; /* Prevent stacking issues */
        }

        /* Only apply inline-block when NOT in preview mode */
        .rich-text-content .interactive-image-container.image-right:not([data-is-previewing="true"]),
        .rich-text-content .image-right:not([data-is-previewing="true"]) {
          display: inline-block !important;
        }

        /* Preview mode override for right alignment - force block display */
        .rich-text-content .interactive-image-container.image-right[data-is-previewing="true"],
        .rich-text-content .image-right[data-is-previewing="true"] {
          display: block !important;
          float: none !important;
          margin-left: auto !important;
          margin-right: 0 !important;
        }

        /* Even more specific override to ensure preview right alignment works */
        .rich-text-content .interactive-image-container[data-is-previewing="true"].image-right {
          display: block !important;
          float: none !important;
          margin: 0.75rem 0 0.75rem auto !important;
        }
        /* Override for right images with explicit dimensions - constrain to 60% max to prevent overflow */
        .rich-text-content .interactive-image-container.image-right.has-explicit-size,
        .rich-text-content .image-right.has-explicit-size {
          max-width: 60% !important; /* Prevent boundary overflow while allowing larger sizes */
          /* Don't override explicit width/height */
        }
          box-sizing: border-box !important;
        }
        .rich-text-content .interactive-image-container.image-full,
        .rich-text-content .image-full {
          display: block !important;
          width: 100% !important;
          max-width: 100% !important;
          margin: 1rem 0 !important;
          float: none !important;
        }
        /* Media Size Classes */
        .rich-text-content .image-small,
        .rich-text-content .video-small {
          max-width: 25% !important;
          width: 25% !important;
        }
        .rich-text-content .image-medium,
        .rich-text-content .video-medium {
          max-width: 50% !important;
          width: 50% !important;
        }
        .rich-text-content .image-large,
        .rich-text-content .video-large {
          max-width: 75% !important;
          width: 75% !important;
        }
        /* Original size uses default styling - no size restrictions */
        .rich-text-content video {
          max-width: 100% !important;
          height: auto !important;
          border-radius: 0.5rem !important;
          margin: 0.5rem 0 !important;
        }
        .rich-text-content audio {
          max-width: 100% !important;
          margin: 0.5rem 0 !important;
        }
        .rich-text-content table {
          border-collapse: collapse !important;
          width: 100% !important;
          margin: 1rem 0 !important;
          border: 1px solid #e5e7eb !important;
        }
        .rich-text-content th, .rich-text-content td {
          border: 1px solid #e5e7eb !important;
          padding: 0.5rem !important;
          text-align: left !important;
        }
        .rich-text-content th {
          background-color: #f9fafb !important;
          font-weight: 600 !important;
        }
        .rich-text-content ul[data-type="taskList"] {
          list-style: none !important;
          padding: 0 !important;
          margin-left: 0 !important;
        }
        .rich-text-content li[data-type="taskItem"] {
          display: flex !important;
          align-items: flex-start !important;
          margin-bottom: 0.25rem !important;
        }
        .rich-text-content input[type="checkbox"] {
          margin-right: 0.5rem !important;
          margin-top: 0.125rem !important;
        }
        .rich-text-content .has-focus {
          border-radius: 3px !important;
          box-shadow: 0 0 0 3px #68d391 !important;
        }
        .rich-text-content .text-align-left {
          text-align: left !important;
        }
        .rich-text-content .text-align-center {
          text-align: center !important;
        }
        .rich-text-content .text-align-right {
          text-align: right !important;
        }
        .rich-text-content .text-align-justify {
          text-align: justify !important;
        }
        .rich-text-content .mention {
          background-color: #dbeafe !important;
          color: #1d4ed8 !important;
          padding: 0.125rem 0.25rem !important;
          border-radius: 0.25rem !important;
          text-decoration: none !important;
        }
        .rich-text-content .hashtag {
          background-color: #dbeafe !important;
          color: #1d4ed8 !important;
          padding: 0.125rem 0.25rem !important;
          border-radius: 0.25rem !important;
          text-decoration: none !important;
          font-weight: 500 !important;
        }
        .mention-item, .hashtag-item {
          display: flex !important;
          align-items: center !important;
          padding: 0.5rem !important;
          cursor: pointer !important;
          border-radius: 0.25rem !important;
        }
        .mention-item:hover, .hashtag-item:hover,
        .mention-item.selected, .hashtag-item.selected {
          background-color: #f3f4f6 !important;
        }
        .mention-item img {
          margin-right: 0.5rem !important;
        }
        .animate-scale-in {
          animation: scaleIn 0.15s ease-out;
        }
        @keyframes scaleIn {
          from {
            transform: scale(0.95);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        /* Audio Container Styles */
        .interactive-audio-container {
          position: relative !important;
          display: block !important;
          max-width: 100% !important;
          box-sizing: border-box !important;
          margin: 1rem 0 !important;
        }

        .interactive-audio-container .audio-wrapper {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
          border-radius: 12px !important;
          padding: 20px !important;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }

        .interactive-audio-container audio {
          width: 100% !important;
          outline: none !important;
        }

        .interactive-audio-container .audio-info {
          display: flex !important;
          align-items: center !important;
          gap: 8px !important;
          margin-top: 12px !important;
          color: white !important;
          font-size: 0.875rem !important;
        }

        .interactive-audio-container:hover .resize-overlay {
          opacity: 1 !important;
        }

        .interactive-audio-container .resize-overlay {
          border-color: #667eea !important;
        }

        .interactive-audio-container .resize-handle {
          background: #667eea !important;
        }

        .interactive-audio-container .drag-handle {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }

        /* Audio alignment classes */
        .audio-left {
          float: left !important;
          margin-right: 1rem !important;
        }

        .audio-right {
          float: right !important;
          margin-left: 1rem !important;
        }

        .audio-center {
          margin: 1rem auto !important;
          float: none !important;
        }

        .audio-full {
          width: 100% !important;
          max-width: 100% !important;
        }

        /* Video Container Styles */
        .interactive-video-container {
          position: relative !important;
          display: block !important;
          max-width: 100% !important;
          box-sizing: border-box !important;
          margin: 1rem 0 !important;
          line-height: 0 !important;
        }

        .interactive-video-container video {
          display: block !important;
          max-width: 100% !important;
          height: auto !important;
          border-radius: 0.5rem !important;
          user-select: none !important;
        }

        .interactive-video-container:hover .resize-overlay {
          opacity: 1 !important;
        }

        .interactive-video-container .resize-overlay {
          border-color: #ef4444 !important;
        }

        .interactive-video-container .resize-handle {
          background: #ef4444 !important;
        }

        .interactive-video-container .drag-handle {
          background: rgba(239, 68, 68, 0.95) !important;
        }

        .interactive-video-container.has-explicit-size video {
          max-width: none !important;
          width: auto !important;
          height: auto !important;
        }

        /* Video alignment classes */
        .video-left {
          display: inline-block !important;
          margin: 0.75rem auto 0.75rem 0 !important;
        }

        .video-right {
          display: inline-block !important;
          margin: 0.75rem 0 0.75rem auto !important;
        }

        .video-center {
          display: block !important;
          margin: 0.5rem auto !important;
          text-align: center !important;
        }

        .video-full {
          display: block !important;
          width: 100% !important;
          max-width: 100% !important;
        }
      `}</style>
      {/* Toolbar */}
      {showToolbar && mode === 'inline' && (
        <div className="border-b border-gray-200 px-2 py-1 relative">
          <div className="flex items-center gap-1">
            {/* Bold */}
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleBold().run()}
              disabled={!editor.can().chain().focus().toggleBold().run()}
              className={`p-1.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                editor.isActive('bold') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Gras (Ctrl+B)"
            >
              <BoldIcon className="w-4 h-4" />
            </button>

            {/* Italic */}
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleItalic().run()}
              disabled={!editor.can().chain().focus().toggleItalic().run()}
              className={`p-1.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                editor.isActive('italic') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Italique (Ctrl+I)"
            >
              <ItalicIcon className="w-4 h-4" />
            </button>

            {/* Link */}
            <button
              type="button"
              onClick={() => {
                const url = window.prompt('URL:');
                if (url) {
                  editor.chain().focus().setLink({ href: url }).run();
                }
              }}
              className={`p-1.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                editor.isActive('link') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Lien (Ctrl+K)"
            >
              <LinkIcon className="w-4 h-4" />
            </button>

            {/* Emoji */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                className="p-1.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                title="Emoji"
              >
                <FaceSmileIcon className="w-4 h-4" />
              </button>

              {/* Emoji Picker for Inline Mode */}
              {showEmojiPicker && (
                <div
                  ref={emojiPickerRef}
                  className="absolute z-50 left-0 top-full mt-2 w-80 max-h-[340px] bg-white border border-gray-200 rounded-xl shadow-xl p-0 text-sm animate-scale-in origin-top-left flex flex-col"
                  role="dialog"
                  aria-label="Emoji picker"
                  onKeyDown={handleEmojiKeyDown}
                >
                  {/* Search */}
                  <div className="px-2 pt-2">
                    <input
                      type="text"
                      value={searchEmoji}
                      onChange={e => { setSearchEmoji(e.target.value); setFocusedEmojiIndex(0); }}
                      placeholder="Search emojis..."
                      className="w-full rounded-md border border-gray-200 px-2 py-1 text-[11px] focus:ring-amber-400 focus:border-amber-400 placeholder-gray-400"
                    />
                  </div>
                  {/* Tabs with window navigation */}
                  <div className="flex items-center gap-1 px-2 pt-2">
                    <button
                      type="button"
                      onClick={handleTabPrev}
                      disabled={emojiTabOffset === 0}
                      className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset === 0 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                      aria-label="Previous emoji categories"
                    >‹</button>
                    <div className="flex items-center gap-1 flex-1" role="tablist">
                      {visibleTabs.map(tab => (
                        <button
                          key={tab}
                          type="button"
                          role="tab"
                          aria-selected={activeEmojiTab === tab}
                          onClick={() => { setActiveEmojiTab(tab); ensureTabVisible(tab); }}
                          className={`flex-1 px-2 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-colors ${activeEmojiTab === tab ? 'bg-amber-200/70 text-amber-800 shadow-inner' : 'hover:bg-amber-50 text-gray-600'} truncate`}
                          title={tab}
                        >{tab}</button>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={handleTabNext}
                      disabled={emojiTabOffset >= EMOJI_TABS.length - 4}
                      className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset >= EMOJI_TABS.length - 4 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                      aria-label="Next emoji categories"
                    >›</button>
                  </div>
                  <div className="mt-2 px-2 pb-2 overflow-y-auto" role="grid">
                    {activeEmojiTab !== 'Recent' && !searchEmoji && (
                      <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1 px-0.5">{activeEmojiTab}</p>
                    )}
                    {currentEmojiSet.length === 0 && (
                      <div className="text-[11px] text-gray-500 py-6 text-center" role="note">No emojis found.</div>
                    )}
                    <div className="flex flex-wrap gap-1" aria-label="Emoji grid">
                      {currentEmojiSet.map((e, i) => e && (
                        <button
                          key={i}
                          type="button"
                          role="gridcell"
                          data-emoji-index={i}
                          tabIndex={i === focusedEmojiIndex ? 0 : -1}
                          aria-label={e.name}
                          title={e.name}
                          onClick={() => { setFocusedEmojiIndex(i); insertEmoji(e.char); }}
                          onFocus={() => setFocusedEmojiIndex(i)}
                          className={`h-7 w-7 flex items-center justify-center rounded-md text-base hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-300 transition ${i === focusedEmojiIndex ? 'ring-1 ring-amber-300' : ''}`}
                        >{e.char}</button>
                      ))}
                    </div>
                    <p className="sr-only">Use arrow keys to navigate. Search by name. Press Enter or Space to select.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Full Toolbar (for full mode) */}
      {showToolbar && mode === 'full' && (
        <div className="border-b border-gray-200 px-1 py-0.5">
          {/* Compact Single Row Layout */}
          <div className="flex flex-wrap items-center gap-0 justify-start">
            {/* Text Formatting Group */}
            <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleBold().run()}
                disabled={!editor.can().chain().focus().toggleBold().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                  editor.isActive('bold') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Gras"
              >
                <BoldIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleItalic().run()}
                disabled={!editor.can().chain().focus().toggleItalic().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                  editor.isActive('italic') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Italique"
              >
                <ItalicIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleUnderline().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive('underline') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Souligné"
              >
                <UnderlineIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleStrike().run()}
                disabled={!editor.can().chain().focus().toggleStrike().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                  editor.isActive('strike') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Barré"
              >
                <StrikethroughIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleCode().run()}
                disabled={!editor.can().chain().focus().toggleCode().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                  editor.isActive('code') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Code en ligne"
              >
                <CodeBracketIcon className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Subscript/Superscript */}
            <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleSubscript().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive('subscript') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Indice"
              >
                <CubeIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleSuperscript().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive('superscript') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Exposant"
              >
                <SparklesIcon className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Lists */}
            <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleBulletList().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive('bulletList') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Liste à puces"
              >
                <ListBulletIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleOrderedList().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive('orderedList') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Liste numérotée"
              >
                <Bars3BottomLeftIcon className="w-3.5 h-3.5" />
              </button>
              {enableAdvancedFeatures && (
                <button
                  type="button"
                  onClick={() => editor.chain().focus().toggleTaskList().run()}
                  className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                    editor.isActive('taskList') ? 'bg-blue-100 text-blue-600' : ''
                  }`}
                  title="Liste de tâches"
                >
                  <CheckIcon className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleBlockquote().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive('blockquote') ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Citation"
              >
                <ChatBubbleLeftRightIcon className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Text Alignment */}
            <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
              <button
                type="button"
                onClick={() => editor.chain().focus().setTextAlign('left').run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive({ textAlign: 'left' }) ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Aligner à gauche"
              >
                <Bars3BottomLeftIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().setTextAlign('center').run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive({ textAlign: 'center' }) ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Centrer"
              >
                <Bars3Icon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().setTextAlign('right').run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive({ textAlign: 'right' }) ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Aligner à droite"
              >
                <Bars3BottomRightIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().setTextAlign('justify').run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive({ textAlign: 'justify' }) ? 'bg-blue-100 text-blue-600' : ''
                }`}
                title="Justifier"
              >
                <Bars4Icon className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Heading Selector - Compact */}
            <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
              <select
                onChange={(e) => {
                  const level = parseInt(e.target.value);
                  if (level === 0) {
                    editor.chain().focus().setParagraph().run();
                  } else {
                    editor.chain().focus().toggleHeading({ level }).run();
                  }
                }}
                value={
                  editor.isActive('heading', { level: 1 }) ? 1 :
                  editor.isActive('heading', { level: 2 }) ? 2 :
                  editor.isActive('heading', { level: 3 }) ? 3 :
                  editor.isActive('heading', { level: 4 }) ? 4 :
                  editor.isActive('heading', { level: 5 }) ? 5 :
                  editor.isActive('heading', { level: 6 }) ? 6 : 0
                }
                className="text-xs border border-gray-300 rounded px-1 py-0.5 max-w-24"
                title="Niveau de titre"
              >
                <option value={0}>Paragraphe</option>
                <option value={1}>Titre 1</option>
                <option value={2}>Titre 2</option>
                <option value={3}>Titre 3</option>
                <option value={4}>Titre 4</option>
                <option value={5}>Titre 5</option>
                <option value={6}>Titre 6</option>
              </select>
            </div>

            {/* Color Tools */}
            <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
              <input
                type="color"
                onInput={(event) => editor.chain().focus().setColor(event.target.value).run()}
                value={editor.getAttributes('textStyle').color || '#000000'}
                data-testid="setColor"
                className="w-6 h-6 border border-gray-300 rounded cursor-pointer"
                title="Couleur du texte"
              />
              <button
                type="button"
                onClick={() => editor.chain().focus().toggleHighlight().run()}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                  editor.isActive('highlight') ? 'bg-yellow-100 text-yellow-600' : ''
                }`}
                title="Surligner"
              >
                <PaintBrushIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().unsetColor().run()}
                className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                title="Réinitialiser la couleur"
              >
                <SwatchIcon className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Advanced Features */}
            {enableAdvancedFeatures && (
              <>
                <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
                  <button
                    type="button"
                    onClick={addCodeBlock}
                    className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                      editor.isActive('codeBlock') ? 'bg-blue-100 text-blue-600' : ''
                    }`}
                    title="Bloc de code"
                  >
                    <DocumentTextIcon className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => editor.chain().focus().setHorizontalRule().run()}
                    className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    title="Ligne horizontale"
                  >
                    <MinusIcon className="w-3.5 h-3.5" />
                  </button>
                  {/* Image Dropdown Menu */}
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setImageDropdownOpen(!imageDropdownOpen)}
                      className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 border border-gray-300 ml-0.5"
                      title="Options d'image"
                    >
                      <PhotoIcon className="w-3.5 h-3.5" />
                      <ChevronDownIcon className="w-2.5 h-2.5 ml-0.5" />
                    </button>

                    {imageDropdownOpen && (
                      <div className="absolute top-full left-0 mt-1 w-48 bg-white rounded-md shadow-lg z-50 border border-gray-200">
                        <div className="py-1">
                          {/* Insert Section */}
                          <div className="px-3 py-1 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-100">
                            Insert
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              addImage();
                              setImageDropdownOpen(false);
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                          >
                            <LinkIcon className="w-4 h-4 mr-2" />
                            Insert Image from URL
                          </button>
                          {enableAdvancedFeatures && (
                            <button
                              type="button"
                              onClick={() => {
                                handleImageUpload();
                                setImageDropdownOpen(false);
                              }}
                              className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                            >
                              <CloudArrowUpIcon className="w-4 h-4 mr-2" />
                              Upload Image File
                            </button>
                          )}

                          {/* Alignment Section */}
                          <div className="px-3 py-1 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-100 mt-2">
                            Alignment
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              alignImageLeft();
                              setImageDropdownOpen(false);
                            }}
                            onMouseEnter={() => previewImageAlignment('left')}
                            onMouseLeave={clearImagePreview}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                          >
                            <ArrowLeftIcon className="w-4 h-4 mr-2" />
                            Align Left
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              alignImageCenter();
                              setImageDropdownOpen(false);
                            }}
                            onMouseEnter={() => previewImageAlignment('center')}
                            onMouseLeave={clearImagePreview}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                          >
                            <Bars3Icon className="w-4 h-4 mr-2" />
                            Center
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              alignImageRight();
                              setImageDropdownOpen(false);
                            }}
                            onMouseEnter={() => previewImageAlignment('right')}
                            onMouseLeave={clearImagePreview}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                          >
                            <ArrowRightIcon className="w-4 h-4 mr-2" />
                            Align Right
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              alignImageFull();
                              setImageDropdownOpen(false);
                            }}
                            onMouseEnter={() => previewImageAlignment('full')}
                            onMouseLeave={clearImagePreview}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                          >
                            <Bars4Icon className="w-4 h-4 mr-2" />
                            Full Width
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={addTable}
                    disabled={editor.isActive('table')}
                    className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                      editor.isActive('table') ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    title={editor.isActive('table') ? "Cannot insert table inside table" : "Insert Table"}
                  >
                    <TableCellsIcon className="w-3.5 h-3.5" />
                  </button>
                </div>
              </>
            )}
            {/* Media Upload - Enhanced with dedicated video/audio buttons */}
            {enableAdvancedFeatures && (
              <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
                <button
                  type="button"
                  onClick={handleVideoUpload}
                  className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 border border-green-200 bg-green-50 hover:bg-green-100"
                  title="Upload Video (Tiptap Style)"
                >
                  <VideoCameraIcon className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={handleAudioUpload}
                  className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 border border-purple-200 bg-purple-50 hover:bg-purple-100"
                  title="Upload Audio (Tiptap Style)"
                >
                  <SpeakerWaveIcon className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={handleGenericFileUpload}
                  className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 border border-orange-200 bg-orange-50 hover:bg-orange-100"
                  title="Upload Files (Tiptap Style)"
                >
                  <CloudArrowUpIcon className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Undo/Redo */}
            <div className="flex items-center border-r border-gray-200 pr-0.5 mr-0.5">
              <button
                type="button"
                onClick={() => editor.chain().focus().undo().run()}
                disabled={!editor.can().chain().focus().undo().run()}
                className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Undo"
              >
                <ArrowUturnLeftIcon className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => editor.chain().focus().redo().run()}
                disabled={!editor.can().chain().focus().redo().run()}
                className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Redo"
              >
                <ArrowUturnRightIcon className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Emoji Picker */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowEmojiPicker(v => !v)}
                className={`p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${showEmojiPicker ? 'bg-amber-100 text-amber-600' : ''}`}
                title="Emoji picker"
              >
                <FaceSmileIcon className="w-3.5 h-3.5" />
              </button>
              {showEmojiPicker && (
                <div
                  ref={emojiPickerRef}
                  className="absolute z-30 right-0 top-full mt-2 w-80 max-h-[340px] bg-white border border-gray-200 rounded-xl shadow-xl p-0 text-sm animate-scale-in origin-top-right flex flex-col"
                  role="dialog"
                  aria-label="Emoji picker"
                  onKeyDown={handleEmojiKeyDown}
                >
                  {/* Search */}
                  <div className="px-2 pt-2">
                    <input
                      type="text"
                      value={searchEmoji}
                      onChange={e => { setSearchEmoji(e.target.value); setFocusedEmojiIndex(0); }}
                      placeholder="Search emojis..."
                      className="w-full rounded-md border border-gray-200 px-2 py-1 text-[11px] focus:ring-amber-400 focus:border-amber-400 placeholder-gray-400"
                    />
                  </div>
                  {/* Tabs with window navigation */}
                  <div className="flex items-center gap-1 px-2 pt-2">
                    <button
                      type="button"
                      onClick={handleTabPrev}
                      disabled={emojiTabOffset === 0}
                      className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset === 0 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                      aria-label="Previous emoji categories"
                    >‹</button>
                    <div className="flex items-center gap-1 flex-1" role="tablist">
                      {visibleTabs.map(tab => (
                        <button
                          key={tab}
                          type="button"
                          role="tab"
                          aria-selected={activeEmojiTab === tab}
                          onClick={() => { setActiveEmojiTab(tab); ensureTabVisible(tab); }}
                          className={`flex-1 px-2 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-colors ${activeEmojiTab === tab ? 'bg-amber-200/70 text-amber-800 shadow-inner' : 'hover:bg-amber-50 text-gray-600'} truncate`}
                          title={tab}
                        >{tab}</button>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={handleTabNext}
                      disabled={emojiTabOffset >= EMOJI_TABS.length - 4}
                      className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset >= EMOJI_TABS.length - 4 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                      aria-label="Next emoji categories"
                    >›</button>
                  </div>
                  <div className="mt-2 px-2 pb-2 overflow-y-auto" role="grid">
                    {activeEmojiTab !== 'Recent' && !searchEmoji && (
                      <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1 px-0.5">{activeEmojiTab}</p>
                    )}
                    {currentEmojiSet.length === 0 && (
                      <div className="text-[11px] text-gray-500 py-6 text-center" role="note">No emojis found.</div>
                    )}
                    <div className="flex flex-wrap gap-1" aria-label="Emoji grid">
                      {currentEmojiSet.map((e, i) => e && (
                        <button
                          key={i}
                          type="button"
                          role="gridcell"
                          data-emoji-index={i}
                          tabIndex={i === focusedEmojiIndex ? 0 : -1}
                          aria-label={e.name}
                          title={e.name}
                          onClick={() => { setFocusedEmojiIndex(i); insertEmoji(e.char); }}
                          onFocus={() => setFocusedEmojiIndex(i)}
                          className={`h-7 w-7 flex items-center justify-center rounded-md text-base hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-300 transition ${i === focusedEmojiIndex ? 'ring-1 ring-amber-300' : ''}`}
                        >{e.char}</button>
                      ))}
                    </div>
                    <p className="sr-only">Use arrow keys to navigate. Search by name. Press Enter or Space to select.</p>
                  </div>
                </div>
              )}
            </div>

            {/* Table Controls and Mentions */}
            <div className="flex items-center">
              {/* Table Dropdown Menu */}
              {enableAdvancedFeatures && editor?.isActive('table') && (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setTableDropdownOpen(!tableDropdownOpen)}
                    className="p-0.5 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 flex items-center"
                    title="Table Actions"
                  >
                    <TableCellsIcon className="w-3.5 h-3.5" />
                    <ChevronDownIcon className="w-2.5 h-2.5 ml-0.5" />
                  </button>

                  {tableDropdownOpen && (
                    <>
                      {/* Backdrop to close dropdown */}
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setTableDropdownOpen(false)}
                      />

                      {/* Dropdown Menu */}
                      <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 min-w-48">
                        <div className="p-1">
                          {/* Row Operations Submenu */}
                          <div className="relative">
                            <button
                              type="button"
                              onClick={() => {
                                setRowSubmenuOpen(!rowSubmenuOpen);
                                setColumnSubmenuOpen(false);
                              }}
                              className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                            >
                              <span>Row Operations</span>
                              <ChevronRightIcon className="w-4 h-4" />
                            </button>

                            {rowSubmenuOpen && (
                              <div className="absolute left-full top-0 ml-1 bg-white border border-gray-200 rounded-md shadow-lg z-30 min-w-40">
                                <div className="p-1">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      addRowAbove();
                                      setTableDropdownOpen(false);
                                    }}
                                    className="w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                                  >
                                    <ArrowUpIcon className="w-4 h-4 mr-2" />
                                    Add Above
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      addRowBelow();
                                      setTableDropdownOpen(false);
                                    }}
                                    className="w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                                  >
                                    <ArrowDownIcon className="w-4 h-4 mr-2" />
                                    Add Below
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      deleteRow();
                                      setTableDropdownOpen(false);
                                    }}
                                    className="w-full flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
                                  >
                                    <TrashIcon className="w-4 h-4 mr-2" />
                                    Delete Row
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Column Operations Submenu */}
                          <div className="relative">
                            <button
                              type="button"
                              onClick={() => {
                                setColumnSubmenuOpen(!columnSubmenuOpen);
                                setRowSubmenuOpen(false);
                              }}
                              className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                            >
                              <span>Column Operations</span>
                              <ChevronRightIcon className="w-4 h-4" />
                            </button>

                            {columnSubmenuOpen && (
                              <div className="absolute left-full top-0 ml-1 bg-white border border-gray-200 rounded-md shadow-lg z-30 min-w-40">
                                <div className="p-1">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      addColumnLeft();
                                      setTableDropdownOpen(false);
                                    }}
                                    className="w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                                  >
                                    <ArrowLeftIcon className="w-4 h-4 mr-2" />
                                    Add Left
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      addColumnRight();
                                      setTableDropdownOpen(false);
                                    }}
                                    className="w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded"
                                  >
                                    <ArrowRightIcon className="w-4 h-4 mr-2" />
                                    Add Right
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      deleteColumn();
                                      setTableDropdownOpen(false);
                                    }}
                                    className="w-full flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
                                  >
                                    <TrashIcon className="w-4 h-4 mr-2" />
                                    Delete Column
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Separator */}
                          <div className="border-t border-gray-100 my-1"></div>

                          {/* Table Actions */}
                          <button
                            type="button"
                            onClick={() => {
                              deleteTable();
                              setTableDropdownOpen(false);
                            }}
                            className="w-full flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
                          >
                            <TrashIcon className="w-4 h-4 mr-2" />
                            Delete Table
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Editor Content with drag & drop */}
      <div
        className={`relative ${isDragging ? 'bg-blue-50 border-blue-300' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {isDragging && (
          <div className="absolute inset-0 flex items-center justify-center bg-blue-50 bg-opacity-90 z-10 border-2 border-dashed border-blue-300">
            <div className="text-center">
              <CloudArrowUpIcon className="w-12 h-12 text-blue-500 mx-auto mb-2" />
              <p className="text-blue-700 font-medium">Drop files here to insert at cursor</p>
              <p className="text-blue-600 text-sm">Images, videos, audio, and PDFs supported</p>
            </div>
          </div>
        )}

        <EditorContent editor={editor} />

        {/* Character Count */}
        {maxLength && (
          <div className="absolute bottom-2 right-3 text-xs font-medium text-gray-400">
            {characterCount}/{maxLength}
          </div>
        )}
      </div>

      {/* Mention Autocomplete Dropdown */}
      {showMentionDropdown && mentionSuggestions.length > 0 && (
        <div
          ref={mentionDropdownRef}
          className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-64 overflow-y-auto min-w-72"
          style={{
            top: `${mentionDropdownPosition.top}px`,
            left: `${mentionDropdownPosition.left}px`,
          }}
        >
          {/* Group suggestions by category */}
          {Object.entries(
            mentionSuggestions.reduce((groups, user, index) => {
              const category = user.category || 'Other';
              if (!groups[category]) {
                groups[category] = [];
              }
              groups[category].push({ ...user, originalIndex: index });
              return groups;
            }, {})
          ).map(([categoryName, categoryUsers]) => (
            <div key={categoryName}>
              {/* Category Header */}
              <div className="px-3 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-100 dark:border-gray-600">
                {categoryName}
              </div>

              {/* Category Users */}
              <ul className="py-1">
                {categoryUsers.map((user, idx) => {
                  const globalIndex = mentionSuggestions.findIndex(u => u.id === user.id);
                  const isSelected = globalIndex === selectedMentionIndex;

                  return (
                    <li
                      key={user.id}
                      className={`px-3 py-2 cursor-pointer flex items-center space-x-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                        isSelected
                          ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                          : 'text-gray-900 dark:text-gray-100'
                      }`}
                      onClick={() => {
                        // Use the stored command function to properly replace the @query with mention
                        if (mentionCommandRef.current) {
                          mentionCommandRef.current({
                            id: user.id,
                            label: user.username,
                          });
                          setShowMentionDropdown(false);
                          setMentionQuery('');
                        }
                      }}
                      onMouseEnter={() => setSelectedMentionIndex(globalIndex)}
                    >
                      <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-sm font-medium flex-shrink-0">
                        {user.avatar_url ? (
                          <img
                            src={user.avatar_url}
                            alt={user.username}
                            className="w-8 h-8 rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-gray-600 dark:text-gray-300">
                            {user.display_name?.charAt(0).toUpperCase() || user.username?.charAt(0).toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">@{user.username}</div>
                        {user.display_name !== user.username && (
                          <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                            {user.display_name}
                          </div>
                        )}
                      </div>
                      {/* Priority badge */}
                      {user.priority === 'follower' && (
                        <div className="text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-1 rounded">
                          Following
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}

          {/* Help text */}
          <div className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
            Use ↑↓ to navigate, Enter to select, Esc to close
          </div>
        </div>
      )}

      {/* Hashtag Autocomplete Dropdown */}
      {showHashtagDropdown && hashtagSuggestions.length > 0 && (
        <div
          ref={hashtagDropdownRef}
          className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-64 overflow-y-auto min-w-72"
          style={{
            top: `${hashtagDropdownPosition.top}px`,
            left: `${hashtagDropdownPosition.left}px`,
          }}
        >
          <ul className="py-1">
            {hashtagSuggestions.map((hashtag, index) => {
              const isSelected = index === selectedHashtagIndex;

              return (
                <li
                  key={hashtag.name}
                  className={`px-3 py-2 cursor-pointer flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                    isSelected
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                      : 'text-gray-900 dark:text-gray-100'
                  }`}
                  onClick={() => {
                    // Use the stored command function to properly replace the #query with hashtag
                    if (hashtagCommandRef.current) {
                      hashtagCommandRef.current({
                        id: hashtag.name,
                        label: hashtag.name,
                      });
                      setShowHashtagDropdown(false);
                      setHashtagQuery('');
                    }
                  }}
                  onMouseEnter={() => setSelectedHashtagIndex(index)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-blue-600 dark:text-blue-400">
                      #{hashtag.name}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {hashtag.is_trending && (
                      <div className="text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 px-2 py-1 rounded">
                        Trending
                      </div>
                    )}
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {hashtag.posts_count} posts
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>

          {/* Help text */}
          <div className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
            Use ↑↓ to navigate, Enter to select, Esc to close
          </div>
        </div>
      )}
    </div>
  );
});

// Add display name for better debugging
RichTextEditor.displayName = 'RichTextEditor';

export default RichTextEditor;
