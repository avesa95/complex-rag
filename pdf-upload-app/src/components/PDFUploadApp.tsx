import React, { useState } from 'react';
import { Upload, File, ExternalLink, Table, Image, Loader, CheckCircle, AlertCircle, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

type Response = {
  answer: string;
  references: {
    tables: {
      element_id: string;
      sub_question: string;
      page_number: number;
      png_file: string;
      html_file: string;
    }[];
    figures: {
      label: string;
      sub_question: string;
      page_number: number;
      png_file: string;
    }[];
  };
};

const PDFUploadApp = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<Response | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [modalImage, setModalImage] = useState<{ src: string; alt: string } | null>(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please select a valid PDF file');
      setSelectedFile(null);
    }
  };

  const handleQuestionChange = (e) => {
    setQuestion(e.target.value);
  };

  const handleQuestionSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please upload a PDF first');
      return;
    }
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }
    setIsLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await fetch('http://localhost:8000/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err.message || 'Failed to get answer');
    } finally {
      setIsLoading(false);
    }
  };

  const formatForLinkedIn = (html: string) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    let olCounter = 1;

    const traverse = (node: Node): string => {
      if (node.nodeType === Node.TEXT_NODE) {
        return node.textContent || "";
      }

      if (node.nodeType !== Node.ELEMENT_NODE) return "";

      const el = node as HTMLElement;
      const tag = el.tagName.toLowerCase();
      const children = Array.from(el.childNodes).map(traverse).join("");

      switch (tag) {
        case "strong":
          return toBoldUnicode(children);
        case "em":
          return toItalicUnicode(children);
        case "s":
          return toStrikethroughUnicode(children);
        case "li": {
          const parent = el.parentElement?.tagName.toLowerCase();
          if (parent === "ul") {
            return `${children}\n`;
          } else if (parent === "ol") {
            const item = `${olCounter}. ${children}\n`;
            olCounter++;
            return item;
          }
          return `${children}\n`;
        }
        case "br":
          return "\n";
        case "p":
        case "div":
          return `${children}\n`;
        case "ul":
        case "ol": {
          if (tag === "ol") olCounter = 1;
          return `${children}\n`; // add newline after whole list block
        }
        default:
          return children;
      }
    };

    return traverse(doc.body)
      .replace(/\n{3,}/g, "\n\n") // prevent extra line breaks
      .trim();
  };

  const toBoldUnicode = (text
  ) => {
    return text.replace(/[A-Za-z0-9]/g, (char) => {
      const code = char.codePointAt(0)!;

      // Uppercase A-Z
      if (code >= 65 && code <= 90)
        return String.fromCodePoint(code + 0x1d400 - 65);
      // Lowercase a-z
      if (code >= 97 && code <= 122)
        return String.fromCodePoint(code + 0x1d41a - 97);
      // Digits 0-9
      if (code >= 48 && code <= 57)
        return String.fromCodePoint(code + 0x1d7ce - 48);

      return char;
    });
  };

  const toItalicUnicode = (text) => {
    return text.replace(/[A-Za-z0-9]/g, (char) =>
      String.fromCodePoint(
        char.codePointAt(0)! + (char >= "a" ? 0x1d622 - 97 : 0x1d608 - 65)
      )
    );
  };

  const toStrikethroughUnicode = (text) => {
    return text.replace(/./g, (char) => char + "̶");
  };

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Image Modal */}
      {modalImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60" onClick={() => setModalImage(null)}>
          <div className="bg-white rounded-lg shadow-lg p-4 relative max-w-3xl w-full flex flex-col items-center" onClick={e => e.stopPropagation()}>
            <button className="absolute top-2 right-2 text-gray-600 hover:text-gray-900 text-2xl font-bold" onClick={() => setModalImage(null)}>&times;</button>
            <img src={modalImage.src} alt={modalImage.alt} className="max-h-[80vh] max-w-full rounded" />
            <div className="mt-2 text-gray-700 text-sm">{modalImage.alt}</div>
          </div>
        </div>
      )}
      {/* Left Side - Response Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-900">PDF Analysis Results</h1>
        </div>
        {/* Response Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!response && !isLoading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <Upload className="mx-auto h-16 w-16 mb-4 text-gray-300" />
                <p className="text-lg">Upload a PDF and ask a question to see results</p>
              </div>
            </div>
          )}
          {isLoading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader className="mx-auto h-8 w-8 animate-spin text-blue-600 mb-4" />
                <p className="text-gray-600">Analyzing...</p>
              </div>
            </div>
          )}
          {response && (
            <div className="space-y-6">
              {/* Answer Section */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4 text-gray-800">Answer</h2>
                <div className="prose max-w-none">
                  <ReactMarkdown>{response.answer as string}</ReactMarkdown>
                </div>
              </div>
              {/* References Section */}
              {response.references && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold mb-4 text-gray-800">References</h2>
                  {/* Tables */}
                  {response.references.tables && response.references.tables.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-md font-medium mb-3 text-gray-700 flex items-center">
                        <Table className="h-4 w-4 mr-2" />
                        Tables
                      </h3>
                      <div className="space-y-3">
                        {response.references.tables.map((table, index) => (
                          <div key={index} className="border border-gray-200 rounded-lg p-3">
                            <p className="font-medium text-gray-900 mb-1 text-sm">{table.element_id}</p>
                            <p className="text-xs text-gray-600 mb-2">{table.sub_question}</p>
                            <div className="flex items-center space-x-3 text-xs text-gray-500">
                              <span>Page {table.page_number}</span>
                              <a 
                                href={`http://localhost:8000/${table.png_file}`} 
                                className="text-blue-600 hover:text-blue-800 flex items-center"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                PNG
                              </a>
                              <a 
                                href={`http://localhost:8000/${table.html_file}`} 
                                className="text-blue-600 hover:text-blue-800 flex items-center"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                HTML
                              </a>
                              {/* Show image preview if png_file exists */}
                              {table.png_file && (
                                <img
                                  src={`http://localhost:8000/${table.png_file}`}
                                  alt={table.element_id}
                                  className="mt-2 max-w-xs border rounded cursor-pointer hover:shadow-lg"
                                  onClick={() => setModalImage({ src: `http://localhost:8000/${table.png_file}`, alt: table.element_id })}
                                />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Figures */}
                  {response.references.figures && response.references.figures.length > 0 && (
                    <div>
                      <h3 className="text-md font-medium mb-3 text-gray-700 flex items-center">
                        <Image className="h-4 w-4 mr-2" />
                        Figures
                      </h3>
                      <div className="space-y-3">
                        {response.references.figures.map((figure, index) => (
                          <div key={index} className="border border-gray-200 rounded-lg p-3">
                            <p className="font-medium text-gray-900 mb-1 text-sm">{figure.label}</p>
                            <p className="text-xs text-gray-600 mb-2">{figure.sub_question}</p>
                            <div className="flex items-center space-x-3 text-xs text-gray-500">
                              <span>Page {figure.page_number}</span>
                              <a 
                                href={`http://localhost:8000/${figure.png_file}`} 
                                className="text-blue-600 hover:text-blue-800 flex items-center"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                View Image
                              </a>
                              {/* Show image preview if png_file exists */}
                              {figure.png_file && (
                                <img
                                  src={`http://localhost:8000/${figure.png_file}`}
                                  alt={figure.label}
                                  className="mt-2 max-w-xs border rounded cursor-pointer hover:shadow-lg"
                                  onClick={() => setModalImage({ src: `http://localhost:8000/${figure.png_file}`, alt: figure.label })}
                                />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      {/* Right Side - Upload & Question Area */}
      <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Upload PDF & Ask</h2>
        </div>
        {/* Upload & Question Content */}
        <div className="flex-1 p-6 flex flex-col space-y-6">
          {/* Upload Area */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
            <Upload className="mx-auto h-10 w-10 text-gray-400 mb-3" />
            <div className="space-y-2">
              <label htmlFor="pdf-upload" className="cursor-pointer">
                <span className="text-sm font-medium text-gray-700">Choose PDF file</span>
                <input
                  id="pdf-upload"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500">Drag and drop or click to browse</p>
            </div>
          </div>
          {/* Selected File */}
          {selectedFile && (
            <div className="p-3 bg-blue-50 rounded-lg flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <File className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900 text-sm">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
          )}
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 rounded-lg flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}
          {/* Question Input */}
          <form onSubmit={handleQuestionSubmit} className="flex flex-col space-y-3">
            <label htmlFor="question" className="text-sm font-medium text-gray-700">Ask a question</label>
            <textarea
              id="question"
              value={question}
              onChange={handleQuestionChange}
              rows={3}
              className="border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
              placeholder="Type your question about the PDF..."
              disabled={!selectedFile || isLoading}
            />
            <button
              type="submit"
              disabled={!selectedFile || !question.trim() || isLoading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span>Ask</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PDFUploadApp;