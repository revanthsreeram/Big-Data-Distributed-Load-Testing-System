import React, { useState } from 'react';
import axios from 'axios';

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

  const handlePostRequest = async () => {
    try {
      const data = {
        'test_id':1,
        'test_type': selectedOption,
        'test_message_delay': parseInt(delay),
        'message_count_per_driver': parseInt(numRequests),
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
          <input type="number" name="delay" value={delay} onChange={handleInputChange} />
        </label>
      </div>
      <div>
        <label>
          Number of Requests:
          <input type="number" name="numRequests" value={numRequests} onChange={handleInputChange} />
        </label>
      </div>
      <button onClick={handlePostRequest}>Post Data</button>
      <p>{postData}</p>
    </div>
  );
};

export default PostComponent;

