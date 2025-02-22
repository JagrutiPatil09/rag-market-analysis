import React, { useState } from "react";
import axios from "axios";

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [fileNames, setFileNames] = useState([]);
  const [uploadResponse, setUploadResponse] = useState("");
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
    setFileNames(files.map(file => file.name));
  };

  const handleFileUpload = async () => {
    if (selectedFiles.length === 0) return alert("Select at least one file!");
    const formData = new FormData();
    selectedFiles.forEach(file => formData.append("file", file));
    try {
      const res = await axios.post("http://127.0.0.1:8000/upload/", formData);
      setUploadResponse(res.data.text_preview || "Files uploaded successfully!");
    } catch {
      setUploadResponse("Error uploading files.");
    }
  };

  const handleProcessPDF = async () => {
    setProcessing(true);
    try {
      const res = await axios.post("http://127.0.0.1:8000/process/");
      if (res.data.error) {
        alert(res.data.error);
      } else {
        alert(res.data.message);
      }
    } catch (error) {
      console.error("Error processing PDFs:", error);
      alert("Error processing files.");
    }
    setProcessing(false);
  };

  const handleQuery = async () => {
    if (!query.trim()) return alert("Enter a query!");
    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:8000/query/", { user_query: query });
      setResponse(res.data.response);
    } catch {
      setResponse("Error querying the document.");
    }
    setLoading(false);
  };

  return (
    <div className="container" style={{ padding: "20px" }}>
      <h1>AI-Powered Document Analysis</h1>

      <section>
        <h2>Upload PDFs</h2>
        <input type="file" multiple onChange={handleFileChange} />
        <button onClick={handleFileUpload}>Upload</button>
        <p>{uploadResponse}</p>
      </section>

      <section>
        <h2>Process PDFs</h2>
        <button onClick={handleProcessPDF} disabled={processing}>
          {processing ? "Processing..." : "Process PDFs"}
        </button>
      </section>

      <section>
        <h2>Query Documents</h2>
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button onClick={handleQuery} disabled={loading}>
          {loading ? "Processing..." : "Ask"}
        </button>
        <p><strong>Response:</strong> {response}</p>
      </section>
    </div>
  );
}

export default App;
