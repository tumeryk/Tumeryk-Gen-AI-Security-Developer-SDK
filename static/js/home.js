//Copyright © 2024 Tumeryk, Inc.

document.addEventListener('DOMContentLoaded', function() {
    var elems = document.querySelectorAll('select');
    var instances = M.FormSelect.init(elems);
    
    // Add event listener to the select element
    document.getElementById('configSelect').addEventListener('change', function() {
      var selectedConfig = this.value;

      // Fetch the cookie value
      var proxyCookie = document.cookie.split('; ').find(row => row.startsWith('proxy=')).split('=')[1];

      fetch('/config_id?config_id=' + selectedConfig, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${proxyCookie}`  // Include the proxy cookie in the headers
        }
      }).then(response => response.json())
        .then(data => {
          console.log('Config changed:', data);
        }).catch(error => {
          console.error('Error changing config:', error);
        });
    });
  });