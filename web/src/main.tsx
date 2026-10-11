import "@fontsource/geist-sans/400.css";
import "@fontsource/geist-sans/500.css";
import "@fontsource/geist-sans/600.css";
import "@fontsource/geist-mono/400.css";
import "@fontsource/geist-mono/500.css";
import "./styles.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Attrition } from "./pages/Attrition";
import { Compensation } from "./pages/Compensation";
import { Departments } from "./pages/Departments";
import { Executive } from "./pages/Executive";
import { Method } from "./pages/Method";
import { NotFound } from "./pages/NotFound";
import { Risk } from "./pages/Risk";
import { Tenure } from "./pages/Tenure";

const root = document.getElementById("root");
if (!root) throw new Error("missing #root element");

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/executive" replace />} />
          <Route path="executive" element={<Executive />} />
          <Route path="attrition" element={<Attrition />} />
          <Route path="departments" element={<Departments />} />
          <Route path="compensation" element={<Compensation />} />
          <Route path="tenure" element={<Tenure />} />
          <Route path="risk" element={<Risk />} />
          <Route path="method" element={<Method />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
