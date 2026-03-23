// @ts-check

/**
 * POST a JSON payload to a Genome Forge API endpoint.
 * @param {string} path
 * @param {unknown} body
 * @returns {Promise<any>}
 */
async function callApi(path, body) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

window.callApi = callApi;
