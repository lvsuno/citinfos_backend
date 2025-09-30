import React, { useCallback, useMemo, useState, useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Placeholder } from '@tiptap/extension-placeholder';
import { CharacterCount } from '@tiptap/extension-character-count';
import { TextStyle } from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import { Highlight } from '@tiptap/extension-highlight';
import { TextAlign } from '@tiptap/extension-text-align';
import { Underline } from '@tiptap/extension-underline';

// Heroicons for basic toolbar
import {
  ListBulletIcon,
  Bars3BottomLeftIcon,
  Bars3BottomRightIcon,
  Bars3Icon,
  Bars4Icon,
  PaintBrushIcon,
  SwatchIcon,
  ArrowUturnLeftIcon,
  ArrowUturnRightIcon,
} from '@heroicons/react/24/outline';

// Inline fallback icons for formatting actions
const iconBase = 'w-4 h-4 fill-current';
export const BoldIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M7 4h6a4 4 0 0 1 0 8H7V4Zm0 8h7a4 4 0 0 1 0 8H7v-8Z" />
  </svg>
);

export const ItalicIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M10 4h6l-3 12H7l3-12Z" />
  </svg>
);

export const UnderlineIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M6 19v2h12v-2H6ZM8 3v8c0 2.21 1.79 4 4 4s4-1.79 4-4V3h-2v8c0 1.1-.9 2-2 2s-2-.9-2-2V3H8Z" />
  </svg>
);

export const StrikethroughIcon = (props) => (
  <svg viewBox="0 0 24 24" className={iconBase} {...props}>
    <path d="M3 12h18v2H3v-2ZM7.5 6.5C7.5 4.57 9.07 3 11 3h2c1.93 0 3.5 1.57 3.5 3.5v.5h-2v-.5c0-.83-.67-1.5-1.5-1.5h-2c-.83 0-1.5.67-1.5 1.5S9.17 8 10 8h4c1.93 0 3.5 1.57 3.5 3.5v3c0 1.93-1.57 3.5-3.5 3.5h-4c-1.93 0-3.5-1.57-3.5-3.5v-.5h2v.5c0 .83.67 1.5 1.5 1.5h4c.83 0 1.5-.67 1.5-1.5v-3c0-.83-.67-1.5-1.5-1.5h-4c-1.93 0-3.5-1.57-3.5-3.5Z" />
  </svg>
);

const RichTextEditorLight = ({
  content = '',
  onChange,
  placeholder = 'Start typing...',
  maxLength = 500,
  className = '',
  height = 'h-24',
  editable = true,
}) => {
  const extensions = useMemo(() => [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3], // Only basic heading levels
      },
      bulletList: {
        HTMLAttributes: {
          class: 'prose-bullet-list',
        },
      },
      orderedList: {
        HTMLAttributes: {
          class: 'prose-ordered-list',
        },
      },
      listItem: {
        HTMLAttributes: {
          class: 'prose-list-item',
        },
      },
      // Exclude underline from StarterKit to avoid conflicts
      underline: false,
    }),
    Placeholder.configure({
      placeholder,
    }),
    CharacterCount.configure({
      limit: maxLength,
    }),
    TextStyle,
    Color,
    Highlight.configure({
      multicolor: false,
    }),
    TextAlign.configure({
      types: ['heading', 'paragraph'],
      alignments: ['left', 'center', 'right'],
    }),
    Underline,
  ], [placeholder, maxLength]);

  const editor = useEditor({
    extensions,
    content: content,
    editable: editable,
    onUpdate: ({ editor }) => {
      const content = editor.getHTML();
      onChange && onChange(content);
    },
  });

  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [editor, content]);

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
        .rich-text-content p {
          margin-bottom: 0.5rem !important;
        }
        .rich-text-content h1, .rich-text-content h2, .rich-text-content h3 {
          font-weight: 600 !important;
          margin-top: 1rem !important;
          margin-bottom: 0.5rem !important;
        }
        .rich-text-content h1 {
          font-size: 1.5rem !important;
        }
        .rich-text-content h2 {
          font-size: 1.25rem !important;
        }
        .rich-text-content h3 {
          font-size: 1.125rem !important;
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
        .rich-text-content mark {
          background-color: #fef08a !important;
          padding: 0.125rem 0.25rem !important;
          border-radius: 0.25rem !important;
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
      `}</style>

      {/* Compact Toolbar */}
      <div className="border-b border-gray-200 px-2 py-1">
        <div className="flex flex-wrap items-center gap-1 justify-start">
          {/* Basic Text Formatting */}
          <div className="flex items-center border-r border-gray-200 pr-2 mr-2">
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleBold().run()}
              disabled={!editor.can().chain().focus().toggleBold().run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                editor.isActive('bold') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Bold"
            >
              <BoldIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleItalic().run()}
              disabled={!editor.can().chain().focus().toggleItalic().run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                editor.isActive('italic') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Italic"
            >
              <ItalicIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleUnderline().run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                editor.isActive('underline') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Underline"
            >
              <UnderlineIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleStrike().run()}
              disabled={!editor.can().chain().focus().toggleStrike().run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                editor.isActive('strike') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Strikethrough"
            >
              <StrikethroughIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Lists */}
          <div className="flex items-center border-r border-gray-200 pr-2 mr-2">
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleBulletList().run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                editor.isActive('bulletList') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Bullet List"
            >
              <ListBulletIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleOrderedList().run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                editor.isActive('orderedList') ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Numbered List"
            >
              <Bars3BottomLeftIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Text Alignment */}
          <div className="flex items-center border-r border-gray-200 pr-2 mr-2">
            <button
              type="button"
              onClick={() => editor.chain().focus().setTextAlign('left').run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                editor.isActive({ textAlign: 'left' }) ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Align Left"
            >
              <Bars3BottomLeftIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().setTextAlign('center').run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                editor.isActive({ textAlign: 'center' }) ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Align Center"
            >
              <Bars3Icon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().setTextAlign('right').run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ${
                editor.isActive({ textAlign: 'right' }) ? 'bg-blue-100 text-blue-600' : ''
              }`}
              title="Align Right"
            >
              <Bars3BottomRightIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Heading Selector */}
          <div className="flex items-center border-r border-gray-200 pr-2 mr-2">
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
                editor.isActive('heading', { level: 3 }) ? 3 : 0
              }
              className="text-xs border border-gray-300 rounded px-2 py-1 max-w-20"
              title="Heading Level"
            >
              <option value={0}>Text</option>
              <option value={1}>H1</option>
              <option value={2}>H2</option>
              <option value={3}>H3</option>
            </select>
          </div>

          {/* Color Tools */}
          <div className="flex items-center border-r border-gray-200 pr-2 mr-2">
            <input
              type="color"
              onInput={(event) => editor.chain().focus().setColor(event.target.value).run()}
              value={editor.getAttributes('textStyle').color || '#000000'}
              className="w-6 h-6 border border-gray-300 rounded cursor-pointer"
              title="Text Color"
            />
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleHighlight().run()}
              className={`p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 ml-1 ${
                editor.isActive('highlight') ? 'bg-yellow-100 text-yellow-600' : ''
              }`}
              title="Highlight"
            >
              <PaintBrushIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().unsetColor().run()}
              className="p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              title="Reset Color"
            >
              <SwatchIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Undo/Redo */}
          <div className="flex items-center">
            <button
              type="button"
              onClick={() => editor.chain().focus().undo().run()}
              disabled={!editor.can().chain().focus().undo().run()}
              className="p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Undo"
            >
              <ArrowUturnLeftIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().redo().run()}
              disabled={!editor.can().chain().focus().redo().run()}
              className="p-1 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ml-1"
              title="Redo"
            >
              <ArrowUturnRightIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Editor Content */}
      <div className={`relative ${height} overflow-auto`}>
        <div className="rich-text-content h-full p-3">
          <EditorContent editor={editor} />
        </div>

        {/* Character Count */}
        {maxLength && (
          <div className={`absolute bottom-2 right-3 text-xs font-medium ${
            isOverLimit ? 'text-red-500' : isNearLimit ? 'text-yellow-600' : 'text-gray-400'
          }`}>
            {characterCount}/{maxLength}
          </div>
        )}
      </div>
    </div>
  );
};

export default RichTextEditorLight;