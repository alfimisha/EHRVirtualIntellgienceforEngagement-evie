**EVIE: Autonomous Round-Making Robot for Patient Care**

Nursing homes and understaffed wards need a reliable way to check on patients more often without burning out caregivers. EVIE is an autonomous round-making robot that patrols patient rooms, holds scripted conversations, listens for problems, and compares responses to EHR patterns to dynamically triage who needs attention.

Using a camera and ultrasonic sensors for safe navigation, a microphone + speech-to-text for patient interaction, and an LLM-backed scoring engine connected to the facility’s EHR, EVIE builds a live priority queue and alerts clinicians to changes that matter.

We built a working prototype with:

Arduino drivetrain
Webcam
Ultrasonic sensors
Flask backend
AI scoring pipeline (powered by the latest model of Llama)
EVIE increases check frequency, surfaces subtler trends in vitals and responses, and gives nurses a lightweight, data-driven assistant—so staff can focus on care, not constant rounds.

**Inspiration**
Nursing homes and hospitals often face severe staffing shortages, meaning patients don’t always get the frequent check-ins they need. We wanted to create a tool that could help caregivers by automating rounds, capturing patient input, and surfacing insights from EHR data—so staff can focus on care instead of constant monitoring, while patients still get valuable interaction and reassurance during difficult times.

**Important Facts:**

94% of U.S. nursing homes report staff shortages. (AHCA/NCAL)
30% of nursing homes reported a shortage of nurses or aides in a four-week period. (AARP)
As of early 2022, only ~2% of nursing homes said they were fully staffed. (JAMA Network)
What It Does
EVIE addresses the challenge of understaffed nursing homes and hospitals by automating patient rounds and enhancing communication between patients and caregivers.

**Autonomous Rounds & Patient Interaction**

Navigates through patient areas, stopping safely when near people using facial recognition
Takes in patient EHR records, engages patients about previous issues, records responses via voice detection, and categorizes severity of concerns
AI-Powered Triage & Priority Queue
Our HCP interface redefines patient engagement and monitoring through an intelligent blend of real-time triage, dynamic risk scoring, and adaptive questioning.

Dynamic Risk Scoring: Patient responses are continuously analyzed against synthetic EHR data and global health trends to compute a real-time risk level
Live Priority Queue: Risk scores automatically feed into a constantly updated patient queue, surfacing critical cases first
Proactive Alerts: Staff are notified immediately if a patient’s condition escalates, enabling early intervention
Impact: Together, these features enable care teams to monitor more patients more often, catch health issues earlier, and prioritize interventions with unprecedented precision—turning fragmented data into actionable intelligence.

**How We Built It**

We integrated robotics hardware with AI and healthcare data systems.

Navigation & Sensors
Arduino Uno, motors, and ultrasonic sensors for path following and collision avoidance
Webcam integration for patient recognition
Voice & Interaction
Microphone and speaker for conversations
Speech-to-text pipeline connected to an LLM (via LangChain + Llama) to handle dialogue
Interaction serially communicates with Arduino to queue motion
Patient Data & AI Scoring
Our system combines backend engineering with a multi-agent AI pipeline handling both structured data and natural interaction.

Record Intelligence Agent (LangChain + LLaMA): Generates conversations, asks targeted questions, and identifies possible critical issues (e.g., cardiac events, strokes)
Voice Interaction Agent (Vosk): Real-time speech-to-text capturing patient inputs and feeding them to the record agent
Automated Risk Scoring Models: Synthesizes outputs into a dynamic urgency score balancing self-reported symptoms with structured EHR context
Priority Queue of Criticality: Maintains a live, ranked patient list updated in real time
Dashboard Visualization: Tkinter-based dashboard displaying the queue with continuous updates for staff
This architecture reflects end-to-end LLM engineering: orchestrating multi-modal inputs, chaining AI agents with contextual awareness, and unifying outputs into a real-time clinical triage assistant.

**Design**

Robot chassis: modified open-source CAD designs (SolidWorks + 3D printing)
Shelves and motor holders for component storage, breadboards secured with zip ties
GUI prototype in Figma → displays queued alerts for providers
Challenges We Ran Into
Parsing Data
None of us come from a healthcare background, so determining which information mattered most was difficult
Relied on research papers, open datasets, and patient experiences
Needed to balance clinical accuracy with practical usability for caregivers
AI Scoring & LLM Engineering
Hard to design a clinically meaningful, patient-friendly scoring system
Risk needed to be relative to other patients, not just an isolated score
Avoided frustrating patients by teaching the model to self-assess confidence and stop probing once enough data was collected
Fine-tuned prompting + health trend baselines made the model both thorough and patient-comfort oriented
Integration
Challenges aligning motion control, facial recognition, speech, database, and AI into one system
Issues sourcing motor drivers, microphones, and fitting parts in the chassis
Addressed with 3D-printed custom parts, wiring adjustments, and iterative testing
What’s Next for EVIE (EHR Virtual Intelligence for Engagement)
Advanced Navigation: LiDAR + multi-room mapping for safe, route-based patient engagement
More Human-like Conversations: Fine-tuned medical LLMs for empathetic voice and natural rapport
Expanded Data Sources: Integration with wearable vitals and IoT sensors, plus real EHR records
Scalability:
Cloud-based GUI for multi-nurse environments
On-device intelligence (Raspberry Pi, NVIDIA Jetson, or cloud-hosted models)
