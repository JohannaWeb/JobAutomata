-JOHANNA ALMEIDA
Systems Engineer & Infrastructure Builder
 Porto, Portugal
 https://github.com/JohannaWeb
 https://juntos.chat
 JohannaWebApps@proton.me

EXECUTIVE SUMMARY
Systems engineer with 17 years of programming experience and 9+ years professional background. Built complete infrastructure stacks from first principles: browser engines, language models, cryptographic implementations, and decentralized identity systems.
Specializes in inference optimization (51x speedup achieved), GPU kernel design, and systems architecture for resource-constrained environments.
Recent 46-day intensive sprint produced 38 public repositories, demonstrating extreme output velocity and systems-level thinking. All work documented transparently with an AI-first methodology.
Core focus: Building sovereign computing infrastructure for communities excluded by mainstream tech consolidation.

RECENT WORK (2026)
Sisyphus: Language Model Training from Scratch
PyTorch, Triton, CUDA Kernel Design
 https://github.com/JohannaWeb/Bastion/tree/change-transformer-arquitecture Hacker News: https://news.ycombinator.com/item?id=47674749
25.6M parameter byte-level language model trained from random initialization (no fine-tuning)
Novel HybridAttention architecture (local attention + recurrent state + gating)
51x inference speedup (5.6 tok/s → 286.6 tok/s)
Complexity reduced from O(n²) to O(n·W + n·D)
KV-cache compression with mixed precision
Custom Triton kernels including hand-written backward pass
Trained 30k steps on RTX 4060 Ti (8GB), achieving 2.15 perplexity
Impact:
Ranked #2 on Google for “Hybrid Attention”
Featured in Google AI Overview
Hacker News front page (40+ points)

Aurora: Browser Engine from First Principles
Rust, wgpu, CSS Layout, Parsing
 https://github.com/JohannaWeb/Bastion/tree/main/projects/Aurora
Full browser pipeline: parsing → layout → rendering
Custom HTML parser (no external libraries)
CSS engine (cascade, specificity, inline/block/flex layouts)
GPU rendering pipeline using wgpu
Glyph atlas-based text rendering with correct baseline alignment
Successfully renders real-world static pages
Recognition:
Noticed by Servo core team (Josh Matthews, Nico Burns)

Juntos: Decentralized Real-Time Chat
TypeScript, AT Protocol, WebSockets
 https://github.com/JohannaWeb/ProjectFalcon https://juntos.chat
First real-time decentralized chat on AT Protocol
No centralized relay servers
DID-based identity + cryptographic key management
Built for marginalized communities

ProjectFalcon: JVM AT Protocol SDK & Sovereign Stack
Java 21, Cryptography, Distributed Systems
 https://github.com/JohannaWeb/ProjectFalcon
First native JVM implementation of AT Protocol
ES256K (secp256k1) cryptography built from scratch
Multicodec encoding/decoding
Identity systems: key rotation, delegation, trust resolution
Research Contribution:
Adversarial Trust Protocol (fixes EigenTrust bootstrapping flaw)

46-DAY INTENSIVE SPRINT (Feb–Mar 2026)
 https://github.com/JohannaWeb?tab=repositories
Produced 38 public repositories, including:
Rust-Boy: Game Boy Color emulator (runs Pokémon Crystal)
Chip-8 Emulator: Full instruction set virtual machine
Rsx: Ps1 emulator in rust.
3 research papers on trust systems, discourse systems, and AI alignment
Output velocity: ~3x normal sustained development pace
 Method: AI-first workflow with transparent documentation

TECHNICAL EXPERTISE
Systems & Low-Level
Browser internals: HTML/CSS parsing, layout engines, rendering
GPU programming: wgpu, Vulkan, Triton, CUDA
CPU emulation: MIPS R3000A, instruction sets
Inference optimization: KV-cache, quantization, latency profiling
Machine Learning & AI
PyTorch internals, gradient computation, optimization dynamics
Attention architectures, recurrent systems, gating mechanisms
Inference pipelines: token generation, batching, sampling
Cryptography & Protocols
secp256k1, ES256K, ECDSA
AT Protocol, ActivityPub, W3C DID
Trust systems, reputation models, Sybil resistance
Languages
Primary: Rust, Java, TypeScript, Python
Secondary: C, JavaScript
Infrastructure & Backend
JVM ecosystem: Spring Boot, Quarkus
Kubernetes, AWS, GCP
Kafka, Snowflake, PostgreSQL
Observability: Prometheus, Grafana

PROFESSIONAL EXPERIENCE
Developer
Nearcode Consulting | Jan 2025 – Present
Architected REST/SOAP services for global vehicle data systems
Built Python ingestion pipelines for Snowflake data lakes
Full-stack development across modern stack

Full Stack Engineer
Critical TechWorks (BMW Group) | May 2019 – Jan 2025
Built systems for global vehicle assembly planning
Scaled Kubernetes infrastructure with Quarkus
Delivered zero-downtime database migrations
Defined JVM architecture standards

Full-Stack Web Developer
Glintt | Sep 2017 – May 2019
Full-stack application development
DevOps scripting and production support
Mentored junior developers

Front-End Developer
Digitina | Jan 2017 – May 2017
Developed web components using Polymer, TypeScript, SASS

Web Developer (Internship)
Helppier | Feb 2016 – Aug 2016
React/Redux development
Automated testing
Agile (SCRUM) workflows

RESEARCH & PUBLICATIONS
Adversarial Trust Protocol for Decentralized Identity (2026)
Identity-Driven Discourse Systems (IDDS) (2026)
AI Alignment and Community Care (2026)
 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6468658

EDUCATION
Bachelor of Science in Software Engineering
 Instituto Superior de Engenharia do Porto (ISEP) | 2012–2017
Informatics and Multimedia 
 Colegio de Gaia 2009-2012

LANGUAGES
Portuguese: Native
English: C1 (Advanced)

METHODOLOGY & PHILOSOPHY
AI-First Development
Transparent documentation of AI usage (Claude, Codex, Gemini)
Context window optimization and iterative workflows
Human verification integrated with AI assistance
Infrastructure for Marginalized Communities
Sovereign computing stack (OS, browser, AI, identity)
Community-first, MIT-licensed systems
Focus on autonomy and inclusion

VALIDATION
Hacker News front page (Hybrid Attention)
Google ranking (#2 “Hybrid Attention”)
Servo core team recognition
Strong open-source engagement

