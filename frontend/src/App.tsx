import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Workspace from './pages/workspace/index';
import AgentList from './pages/agents/list';
import AgentConfig from './pages/agents/config';
import Resources from './pages/resources/index';
import Chat from './pages/chat/index';
import Evaluation from './pages/evaluation/index';

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Workspace />} />
          <Route path="/workspace" element={<Workspace />} />
          <Route path="/agents" element={<AgentList />} />
          <Route path="/agents/new" element={<AgentConfig />} />
          <Route path="/agents/:id" element={<AgentConfig />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}