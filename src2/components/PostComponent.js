import React, { useState } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid'; // Import v4 method from uuid package

const PostComponent = () => {
  const [postData, setPostData] = useState('');
  const [selectedOption, setSelectedOption] = useState('avalanche');
  const [delay, setDelay] = useState(0);
  const [numRequests, setNumRequests] = useState('');

  const handleOptionChange = (e) => {
    setSelectedOption(e.target.value);
    if (e.target.value === 'avalanche') {
      setDelay(0);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name === 'delay') {
      setDelay(value);
    } else if (name === 'numRequests') {
      setNumRequests(value);
    }
  };

  const handleStopProcesses = async () => {
    try {
      await axios.post('http://localhost:8001/stop_processes'); // Send POST request to /stop_processes route
      // You might want to handle the response or set some state here after the request is sent successfully
    } catch (error) {
      console.error('Error stopping processes:', error);
    }
  };

  const handlePostRequest = async () => {
    try {
      const testId =  uuidv4(); // Generate a unique test_id using uuid
      const data = {
        test_id: testId,
        test_type: selectedOption,
        test_message_delay: parseInt(delay),
        message_count_per_driver: parseInt(numRequests),
      };

      const response = await axios.post('http://localhost:8001/send_trigger', data); // Replace with your API endpoint
      setPostData(response.data);
    } catch (error) {
      console.error('Error posting data:', error);
    }
  };

  return (
    <div>
      <h2>Post Data</h2>
      <div>
        <label>
          <input
            type="radio"
            value="avalanche"
            checked={selectedOption === 'avalanche'}
            onChange={handleOptionChange}
          />
          Avalanche
        </label>
        <label>
          <input
            type="radio"
            value="tsunami"
            checked={selectedOption === 'tsunami'}
            onChange={handleOptionChange}
          />
          Tsunami
        </label>
      </div>
      <div>
        <label>
          Delay:
          <input type="number" name="delay" value={delay} onChange={handleInputChange} min={0} />
        </label>
      </div>
      <div>
        <label>
          Number of Requests:
          <input type="number" name="numRequests" value={numRequests} onChange={handleInputChange} min={0} />
        </label>
      </div>
      <button onClick={handlePostRequest}>Post Data</button>
      <button onClick={handleStopProcesses}>Stop Processes</button>
      <p>{postData}</p>
    </div>
  );
};

export default PostComponent;

