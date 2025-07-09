import React, { useState } from 'react';
import { Upload, File, ExternalLink, Table, Image, Loader, CheckCircle, AlertCircle } from 'lucide-react';

const PDFUploadApp = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

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

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a PDF file first');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('pdf', selectedFile);

      // Replace with your actual endpoint
      const response = await fetch('/api/analyze-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResponse(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze PDF');
      // For demo purposes, show sample response
      setResponse({
        answer: "# Engine Exhaust System Overview\n\nBased on the service manual information provided, here's a comprehensive overview of the engine exhaust system:\n\n## Main Components of the Engine Exhaust System\n\nThe engine exhaust system consists of several key components:\n\n1. **Tail pipe** - Connected to the system with clamps\n2. **Clamps** - Used to secure the tail pipe and other components\n3. **Flex pipe assembly** - A flexible section that allows for movement\n4. **SCR (Selective Catalytic Reduction) assembly** - Part of the emissions control system\n5. **Muffler system** - For noise reduction\n6. **Belly pans** - Protective covers that must be removed for exhaust system access\n\nFor machines equipped with Ultra-Low Sulfur (ULS) capability (110hp/82kW or 130hp/97kW), the system includes additional components related to emissions control.\n\n## Safety Considerations and Requirements\n\nThe service manual emphasizes several important safety considerations:\n\n1. **General safety practices**: Follow all safety precautions outlined in Section 1, \"Safety Practices\" of the manual.\n\n2. **Emission-sensitive components**: The exhaust assembly is emission-sensitive and must be replaced exactly as removed. Contact your local JLG dealer before removing the muffler system.\n\n3. **Flex pipe handling**: When removing or installing the flex pipe assembly, DO NOT apply excessive force to the flex section that could over-extend, compress, or twist the flex.\n\n4. **System cooling**: Allow system fluids to cool before working on the exhaust system.\n\n5. **Battery disconnection**: Properly disconnect the battery before servicing the exhaust system.\n\n6. **Fire safety**: Have an assistant stand by with a Class B fire extinguisher during certain maintenance procedures.\n\n7. **Legal compliance**: In territories where legal requirements govern engine smoke emission, noise, and safety factors, all maintenance and repairs must comply with local regulations.\n\n## Maintenance Procedures\n\nThe service manual outlines several maintenance procedures for the exhaust system:\n\n### Removal Procedure (for ULS-equipped models):\n1. Park machine on a firm, level surface, level machine, fully retract boom, lower boom, place transmission in (N) NEUTRAL, engage park brake, and shut engine OFF.\n2. Place a Do Not Operate Tag on both ignition key switch and steering wheel.\n3. Open engine cover and allow system fluids to cool.\n4. Properly disconnect battery (refer to Section 9.8, 'Battery').\n5. Remove belly pans.\n6. Loosen and remove clamps at tail pipe.\n7. Remove tail pipe.",
        references: {
          tables: [
            {
              sub_question: "What are the main components of the engine exhaust system?",
              element_id: "table-175-1",
              page_number: "175",
              png_file: "scratch/service_manual_long/page_175/tables/table-175-1.png",
              html_file: "scratch/service_manual_long/page_175/tables/table-175-1.html"
            },
            {
              sub_question: "What are the safety considerations and requirements for the engine exhaust system?",
              element_id: "table-27-1",
              page_number: "27",
              png_file: "scratch/service_manual_long/page_27/tables/table-27-1.png",
              html_file: "scratch/service_manual_long/page_27/tables/table-27-1.html"
            },
            {
              sub_question: "What maintenance procedures are required for the engine exhaust system?",
              element_id: "table-510-1",
              page_number: "510",
              png_file: "scratch/service_manual_long/page_510/tables/table-510-1.png",
              html_file: "scratch/service_manual_long/page_510/tables/table-510-1.html"
            }
          ],
          figures: [
            {
              sub_question: "What are the main components of the engine exhaust system?",
              label: "figure-199-1",
              page_number: "199",
              png_file: "scratch/service_manual_long/page_199/images/image-199-1.png"
            },
            {
              sub_question: "What are the main components of the engine exhaust system?",
              label: "figure-199-2",
              page_number: "199",
              png_file: "scratch/service_manual_long/page_199/images/image-199-2.png"
            },
            {
              sub_question: "What are the safety considerations and requirements for the engine exhaust system?",
              label: "figure-197-1",
              page_number: "197",
              png_file: "scratch/service_manual_long/page_197/images/image-197-1.png"
            }
          ]
        }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatMarkdown = (text) => {
    return text
      .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mb-4 text-gray-800">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold mb-3 text-gray-700">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold mb-2 text-gray-700">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
      .replace(/^\d+\. (.*$)/gm, '<li class="mb-1">$1</li>')
      .replace(/\n\n/g, '</p><p class="mb-3">')
      .replace(/^(?!<[h|l])/gm, '<p class="mb-3">')
      .replace(/<\/p><p class="mb-3">(<li)/g, '<ul class="list-decimal list-inside mb-4">$1')
      .replace(/(<\/li>)(?!<li)/g, '$1</ul><p class="mb-3">');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">PDF Analysis Tool</h1>
          <p className="text-gray-600">Upload a PDF document to get detailed analysis and references</p>
        </div>

        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <div className="space-y-2">
              <label htmlFor="pdf-upload" className="cursor-pointer">
                <span className="text-lg font-medium text-gray-700">Choose PDF file</span>
                <input
                  id="pdf-upload"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
              <p className="text-sm text-gray-500">Drag and drop or click to browse</p>
            </div>
          </div>

          {selectedFile && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <File className="h-8 w-8 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 rounded-lg flex items-center space-x-3">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!selectedFile || isLoading}
            className="w-full mt-6 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <Loader className="h-5 w-5 animate-spin" />
                <span>Analyzing PDF...</span>
              </>
            ) : (
              <span>Analyze PDF</span>
            )}
          </button>
        </div>

        {/* Response Section */}
        {response && (
          <div className="space-y-6">
            {/* Answer Section */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Analysis Results</h2>
              <div 
                className="prose max-w-none"
                dangerouslySetInnerHTML={{ __html: formatMarkdown(response.answer) }}
              />
            </div>

            {/* References Section */}
            {response.references && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">References</h2>
                
                {/* Tables */}
                {response.references.tables && response.references.tables.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium mb-3 text-gray-700 flex items-center">
                      <Table className="h-5 w-5 mr-2" />
                      Tables
                    </h3>
                    <div className="space-y-3">
                      {response.references.tables.map((table, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <p className="font-medium text-gray-900 mb-2">{table.element_id}</p>
                          <p className="text-sm text-gray-600 mb-2">{table.sub_question}</p>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>Page {table.page_number}</span>
                            <a 
                              href={table.png_file} 
                              className="text-blue-600 hover:text-blue-800 flex items-center"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              View PNG
                            </a>
                            <a 
                              href={table.html_file} 
                              className="text-blue-600 hover:text-blue-800 flex items-center"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              View HTML
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Figures */}
                {response.references.figures && response.references.figures.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium mb-3 text-gray-700 flex items-center">
                      <Image className="h-5 w-5 mr-2" />
                      Figures
                    </h3>
                    <div className="space-y-3">
                      {response.references.figures.map((figure, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <p className="font-medium text-gray-900 mb-2">{figure.label}</p>
                          <p className="text-sm text-gray-600 mb-2">{figure.sub_question}</p>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>Page {figure.page_number}</span>
                            <a 
                              href={figure.png_file} 
                              className="text-blue-600 hover:text-blue-800 flex items-center"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              View Image
                            </a>
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
  );
};

export default PDFUploadApp;