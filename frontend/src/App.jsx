import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'

function App() {
  return (
    <div className="min-h-screen">
      <nav className="bg-blue-600 text-white p-4 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Tiger Trade & DeepSeek Bot</h1>
          <div className="text-sm">Status: <span className="font-bold text-green-300">Active</span></div>
        </div>
      </nav>
      <main className="container mx-auto p-4">
        <Dashboard />
      </main>
    </div>
  )
}

export default App

