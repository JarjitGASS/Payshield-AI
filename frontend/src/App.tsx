import { BrowserRouter, Route, Routes } from "react-router-dom";
import HomePage from "./pages/home.page";
import LoginPage from "./pages/login.page";
import RegisterPage from "./pages/register.page";
import BindEmailPage from "./pages/bindemail.page";
import NameEntropyPage from "./pages/nameEntropy.page";
import GeoIpPage from "./pages/geoIp.page";
import SentimentEntityPage from "./pages/sentimentEntity.page";
import NetworkFraudPage from "./pages/networkFraud.page";
import ClickTestPage from "./pages/clickTest.page";
import AgenticRiskAssessmentPage from "./pages/agenticRiskAssessment.page";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/bind-email" element={<BindEmailPage />} />
        <Route path="/name-entropy" element={<NameEntropyPage />} />
        <Route path="/geo-ip" element={<GeoIpPage />} />
        <Route path="/sentiment-entity" element={<SentimentEntityPage />} />
        <Route path="/network-fraud" element={<NetworkFraudPage />} />
        <Route path="/click-test" element={<ClickTestPage />} />
        <Route path="/agentic-risk-assessment" element={<AgenticRiskAssessmentPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
