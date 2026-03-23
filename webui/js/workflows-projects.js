async function runWorkspaceCreate() {
  try {
    const members = document.getElementById('workspaceMembers').value.split(',').map((s) => s.trim()).filter(Boolean);
    show(await callApi('/api/workspace-create', {
      workspace_name: document.getElementById('workspaceName').value,
      owner: document.getElementById('workspaceOwner').value,
      members,
    }));
  } catch (e) { show(String(e)); }
}

async function runProjectPermissionsSet() {
  try {
    const project_name = document.getElementById('permProjectName').value;
    const user = document.getElementById('permUser').value;
    const role = document.getElementById('permRole').value;
    show(await callApi('/api/project-permissions', { project_name, roles: { [user]: role } }));
  } catch (e) { show(String(e)); }
}

async function runProjectPermissionsGet() {
  try {
    const project_name = document.getElementById('permProjectName').value;
    show(await callApi('/api/project-permissions', { project_name }));
  } catch (e) { show(String(e)); }
}

async function runProjectAuditLogGet() {
  try {
    const project_name = document.getElementById('permProjectName').value;
    show(await callApi('/api/project-audit-log', { project_name, limit: 200 }));
  } catch (e) { show(String(e)); }
}

async function runProjectDiff() {
  try {
    const project_name_b = document.getElementById('permProjectName').value;
    show(await callApi('/api/project-diff', {
      project_name_a: document.getElementById('projectName').value,
      project_name_b,
    }));
  } catch (e) { show(String(e)); }
}

async function runReviewSubmit() {
  try {
    const r = await callApi('/api/review-submit', {
      project_name: document.getElementById('reviewProjectName').value,
      submitter: document.getElementById('reviewSubmitter').value,
      summary: document.getElementById('reviewSummary').value,
    });
    document.getElementById('reviewId').value = r.review?.review_id || '';
    show(r);
  } catch (e) { show(String(e)); }
}

async function runReviewApprove() {
  try {
    show(await callApi('/api/review-approve', {
      review_id: document.getElementById('reviewId').value,
      project_name: document.getElementById('reviewProjectName').value,
      reviewer: document.getElementById('reviewerName').value,
      note: document.getElementById('reviewNote').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runProjectSave() {
  try {
    const history = historyState.stack.slice(0, historyState.index + 1);
    show(await callApi('/api/project-save', payload({
      project_name: document.getElementById('projectName').value,
      history,
      features: featureState,
    })));
  } catch (e) { show(String(e)); }
}

async function runProjectLoad() {
  try {
    const r = await callApi('/api/project-load', {
      project_name: document.getElementById('projectName').value,
    });
    document.getElementById('name').value = r.name || r.project_name || 'LoadedProject';
    document.getElementById('content').value = r.content || '';
    if (r.topology) document.getElementById('topology').value = r.topology;
    featureState = Array.isArray(r.features) ? r.features : [];
    historyState.stack = Array.isArray(r.history) && r.history.length ? r.history : [document.getElementById('content').value];
    historyState.index = historyState.stack.length - 1;
    runInfo();
    show(r);
  } catch (e) { show(String(e)); }
}

async function runProjectList() {
  try {
    show(await callApi('/api/project-list', {}));
  } catch (e) { show(String(e)); }
}

async function runProjectDelete() {
  try {
    show(await callApi('/api/project-delete', {
      project_name: document.getElementById('projectName').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runCollectionSave() {
  try {
    show(await callApi('/api/collection-save', {
      collection_name: document.getElementById('collectionName').value,
      projects: document.getElementById('collectionProjects').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runCollectionLoad() {
  try {
    const r = await callApi('/api/collection-load', {
      collection_name: document.getElementById('collectionName').value,
    });
    document.getElementById('collectionProjects').value = (r.projects || []).join(',');
    show(r);
  } catch (e) { show(String(e)); }
}

async function runCollectionList() {
  try {
    show(await callApi('/api/collection-list', {}));
  } catch (e) { show(String(e)); }
}

async function runCollectionDelete() {
  try {
    show(await callApi('/api/collection-delete', {
      collection_name: document.getElementById('collectionName').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runCollectionAddProject() {
  try {
    show(await callApi('/api/collection-add-project', {
      collection_name: document.getElementById('collectionName').value,
      project_name: document.getElementById('projectName').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runShareCreate() {
  try {
    const r = await callApi('/api/share-create', {
      projects: document.getElementById('collectionProjects').value,
      collection_name: document.getElementById('collectionName').value,
      include_content: true,
    });
    document.getElementById('shareId').value = r.share_id || '';
    show(r);
  } catch (e) { show(String(e)); }
}

async function runShareLoad() {
  try {
    show(await callApi('/api/share-load', {
      share_id: document.getElementById('shareId').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runProjectHistoryGraph() {
  try {
    const r = await callApi('/api/project-history-svg', {
      project_name: document.getElementById('projectName').value,
    });
    document.getElementById('historyGraph').innerHTML = r.svg || '';
    show(r);
  } catch (e) { show(String(e)); }
}
