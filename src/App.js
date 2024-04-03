import logo from './logo.svg';
import './App.css';
import LiveComponent from './components/LiveComponent';
import GetComponent from './components/GetComponent';
import PostComponent from './components/PostComponent';

import React, { useState } from 'react';
import axios from 'axios';

const NumberInputComponent = ({ setApiSuccess }) => {
  const [number, setNumber] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://127.0.0.1:8001/process_number', { number });
      if (response.status === 200) {
        // If successful response received, set the success state to render components
        setApiSuccess(true);
      }
    } catch (error) {
      // Handle error responses here if needed
      console.error('Error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="number"
        value={number}
        onChange={(e) => setNumber(e.target.value)}
        placeholder="Enter a number"
      />
      <button type="submit">Submit</button>
    </form>
  );
};

const App = () => {
  const [apiSuccess, setApiSuccess] = useState(false);

  return (
    <div>
      {!apiSuccess && <NumberInputComponent setApiSuccess={setApiSuccess} />}
      {apiSuccess && (
        <div>
      		<LiveComponent />
      		<GetComponent />
      		<PostComponent />
    	</div>
      )}
    </div>
  );
};

export default App;

