import { Canvas } from '@react-three/fiber'
import { OrbitControls, Text, RoundedBox, Line } from '@react-three/drei'
import { useState, useRef, useMemo } from 'react'
import * as THREE from 'three'

interface Agent {
  name: string
  color: string
  position: [number, number, number]
  icon: string
  status: 'idle' | 'working' | 'completed'
  description: string
}

const agents: Agent[] = [
  {
    name: 'Crawler Agent',
    color: '#f5576c',
    position: [-8, 2, 0],
    icon: '🕷️',
    status: 'working',
    description: 'Autonomously crawls websites using LLM reasoning'
  },
  {
    name: 'Extractor Agent',
    color: '#00f2fe',
    position: [-4, 2, 0],
    icon: '🔧',
    status: 'idle',
    description: 'Extracts and structures content from raw HTML'
  },
  {
    name: 'Memory System',
    color: '#4facfe',
    position: [0, 2, 0],
    icon: '🧠',
    status: 'idle',
    description: 'FAISS vector storage for duplicate detection'
  },
  {
    name: 'Writer Agent',
    color: '#43e97b',
    position: [4, 2, 0],
    icon: '✍️',
    status: 'idle',
    description: 'Generates original blog posts using Gemma/Ollama'
  },
  {
    name: 'Editor Agent',
    color: '#fee140',
    position: [8, 2, 0],
    icon: '✏️',
    status: 'idle',
    description: 'Improves readability and quality'
  },
  {
    name: 'Reviewer Agent',
    color: '#a8edea',
    position: [4, -2, 0],
    icon: '🔍',
    status: 'idle',
    description: 'Validates content originality'
  },
  {
    name: 'Publisher Agent',
    color: '#d299c2',
    position: [-4, -2, 0],
    icon: '📤',
    status: 'idle',
    description: 'Publishes to Medium or saves as local draft'
  }
]

function AgentNode({ agent, isActive }: { agent: Agent; isActive: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)
  
  // Pulsing animation for active agents
  const scale = isActive ? 1.2 + Math.sin(Date.now() * 0.005) * 0.1 : 1

  return (
    <group position={agent.position}>
      {/* Agent Box */}
      <RoundedBox
        ref={meshRef}
        args={[2, 1.5, 1]}
        radius={0.1}
        smoothness={4}
        scale={scale}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={agent.color}
          emissive={isActive ? agent.color : '#000000'}
          emissiveIntensity={isActive ? 0.5 : 0.1}
          metalness={0.5}
          roughness={0.3}
        />
      </RoundedBox>

      {/* Agent Icon */}
      <Text
        position={[0, 0, 0.6]}
        fontSize={0.5}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {agent.icon}
      </Text>

      {/* Agent Name */}
      <Text
        position={[0, -1.2, 0]}
        fontSize={0.25}
        color={hovered ? agent.color : 'white'}
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        {agent.name}
      </Text>

      {/* Status Indicator */}
      {isActive && (
        <mesh position={[0.8, 0.8, 0.6]}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial color="#43e97b" emissive="#43e97b" emissiveIntensity={1} />
        </mesh>
      )}
    </group>
  )
}

function ConnectionLine({ start, end, isActive }: { 
  start: [number, number, number]
  end: [number, number, number]
  isActive: boolean
}) {
  const points = useMemo(() => {
    const segments = 20
    const result = []
    for (let i = 0; i <= segments; i++) {
      const t = i / segments
      const x = start[0] + (end[0] - start[0]) * t
      const y = start[1] + (end[1] - start[1]) * t
      const z = start[2] + (end[2] - start[2]) * t
      result.push(new THREE.Vector3(x, y, z))
    }
    return result
  }, [start, end])

  return (
    <Line
      points={points}
      color={isActive ? '#667eea' : 'rgba(255,255,255,0.1)'}
      lineWidth={isActive ? 3 : 1}
      transparent
      opacity={isActive ? 1 : 0.3}
    />
  )
}

function ParticleSystem({ active }: { active: boolean }) {
  const particlesRef = useRef<THREE.Points>(null)
  
  const positions = useMemo(() => {
    const positions = new Float32Array(100 * 3)
    for (let i = 0; i < 100; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 30
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10
    }
    return positions
  }, [])

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={100}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color="#667eea"
        transparent
        opacity={active ? 0.8 : 0.2}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

function Scene({ currentStep }: { currentStep: number }) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, 10]} intensity={0.5} color="#667eea" />
      
      {/* Background Particles */}
      <ParticleSystem active={currentStep > 0} />
      
      {/* Agents */}
      {agents.map((agent, index) => (
        <AgentNode
          key={agent.name}
          agent={agent}
          isActive={index === currentStep}
        />
      ))}

      {/* Connection Lines */}
      <ConnectionLine
        start={agents[0].position}
        end={agents[1].position}
        isActive={currentStep === 0}
      />
      <ConnectionLine
        start={agents[1].position}
        end={agents[2].position}
        isActive={currentStep === 1}
      />
      <ConnectionLine
        start={agents[2].position}
        end={agents[3].position}
        isActive={currentStep === 2}
      />
      <ConnectionLine
        start={agents[3].position}
        end={agents[4].position}
        isActive={currentStep === 3}
      />
      <ConnectionLine
        start={agents[4].position}
        end={agents[5].position}
        isActive={currentStep === 4}
      />
      <ConnectionLine
        start={agents[5].position}
        end={agents[6].position}
        isActive={currentStep === 5}
      />

      {/* Floor Grid */}
      <gridHelper args={[30, 30, 0x667eea, 0x222244]} position={[0, -3, 0]} />
      
      {/* Camera Controls */}
      <OrbitControls
        enableZoom={true}
        enablePan={true}
        minDistance={5}
        maxDistance={30}
      />
    </>
  )
}

export default function AgentVisualization() {
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  const stepDescriptions = [
    'Crawler Agent is navigating websites using LLM reasoning',
    'Extractor Agent is cleaning and structuring content',
    'Memory System is checking for duplicates',
    'Writer Agent is generating original blog post',
    'Editor Agent is improving quality',
    'Reviewer Agent is validating originality',
    'Publisher Agent is saving the draft'
  ]

  return (
    <main className="main-content">
      <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem' }}>
        🎮 3D Agent Workflow Visualization
      </h1>
      <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '2rem' }}>
        Watch how autonomous agents collaborate to generate blog posts
      </p>

      {/* Controls */}
      <div style={{ marginBottom: '2rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <button
          className="btn"
          onClick={() => setIsPlaying(!isPlaying)}
        >
          {isPlaying ? '⏸️ Pause' : '▶️ Play Animation'}
        </button>
        <button
          className="btn"
          onClick={() => setCurrentStep(0)}
          style={{ background: 'rgba(255,255,255,0.1)' }}
        >
          🔄 Reset
        </button>
        <div style={{ marginLeft: 'auto', color: 'rgba(255,255,255,0.6)' }}>
          Step {currentStep + 1} of 7: {stepDescriptions[currentStep]}
        </div>
      </div>

      {/* 3D Canvas */}
      <div className="canvas-container">
        <Canvas
          camera={{ position: [0, 5, 15], fov: 60 }}
          style={{ background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%)' }}
        >
          <Scene currentStep={currentStep} />
        </Canvas>
      </div>

      {/* Agent Status Cards */}
      <div className="agent-status">
        {agents.map((agent, index) => (
          <div key={agent.name} className="agent-card">
            <div className={`agent-icon agent-${agent.name.split(' ')[0].toLowerCase()}`}>
              {agent.icon}
            </div>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>{agent.name}</h3>
            <p style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.6)' }}>
              {agent.description}
            </p>
            <div style={{
              marginTop: '0.5rem',
              padding: '0.25rem 0.75rem',
              borderRadius: '20px',
              background: index === currentStep ? 'rgba(102, 126, 234, 0.3)' : 'rgba(255,255,255,0.1)',
              color: index === currentStep ? '#667eea' : 'rgba(255,255,255,0.5)',
              fontSize: '0.75rem',
              fontWeight: 600
            }}>
              {index === currentStep ? '⚡ Active' : index < currentStep ? '✅ Done' : '⏳ Waiting'}
            </div>
          </div>
        ))}
      </div>
    </main>
  )
}
