# PromptFlow User Guide

Welcome to PromptFlow! This guide will help you get started with creating and managing AI agents through our visual interface.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Your First Agent](#creating-your-first-agent)
3. [Managing Workspaces](#managing-workspaces)
4. [Working with Datasets](#working-with-datasets)
5. [Running Agents](#running-agents)
6. [Collaboration Features](#collaboration-features)

## Getting Started

### Account Setup

1. **Sign Up**: Visit the PromptFlow application and click "Sign Up"
2. **Create Account**: Enter your email, name, and password
3. **Verify Email**: Check your inbox for verification email
4. **Login**: Use your credentials to access the dashboard

### First Steps

After logging in, you'll see the dashboard with:
- **My Workspaces**: Your personal work area
- **Quick Actions**: Create agent, upload documents
- **Recent Activity**: Latest agent runs and updates

## Creating Your First Agent

### Step 1: Choose a Workspace

1. From the dashboard, select or create a workspace
2. Workspaces help organize your agents and datasets
3. Each workspace can have multiple agents and datasets

### Step 2: Create a New Agent

1. Click "Create Agent" in your workspace
2. Fill in basic information:
   - **Name**: Descriptive name for your agent
   - **Description**: What this agent does
   - **Category**: Type of task (e.g., Customer Support, Data Analysis)

### Step 3: Design Your Agent Workflow

The visual canvas allows you to build AI workflows by connecting nodes:

#### Available Node Types

**1. Input Node**
- Purpose: Starting point for your agent
- Configuration: Define input parameters
- Usage: Every agent starts with an input node

**2. LLM Node**
- Purpose: Language model processing
- Configuration:
  - Model selection (GPT-4, Claude, Llama, etc.)
  - Temperature setting
  - Max tokens
  - System prompt
- Usage: Core AI processing

**3. Retrieval Node**
- Purpose: Retrieve relevant information from datasets
- Configuration:
  - Dataset selection
  - Number of results
  - Similarity threshold
- Usage: RAG (Retrieval-Augmented Generation)

**4. Tool Node**
- Purpose: Execute external tools or APIs
- Configuration:
  - Tool type (HTTP, Database, Custom)
  - Parameters
  - Authentication
- Usage: External integrations

**5. Transformation Node**
- Purpose: Process and transform data
- Configuration:
  - Transformation type
  - Mapping rules
  - Validation
- Usage: Data manipulation

**6. Output Node**
- Purpose: Final result delivery
- Configuration:
  - Output format
  - Response template
- Usage: Agent result

#### Connecting Nodes

1. **Drag nodes** from the sidebar to the canvas
2. **Connect nodes** by clicking and dragging from output ports to input ports
3. **Configure nodes** by double-clicking on them
4. **Test workflow** using the preview feature

### Step 4: Test Your Agent

1. Click "Test Run" in the agent editor
2. Enter sample input data
3. Watch the execution flow in real-time
4. Review the output results
5. Iterate and improve the workflow

## Managing Workspaces

### Creating Workspaces

1. Click "New Workspace" from the workspace selector
2. Fill in workspace details:
   - **Name**: Workspace identifier
   - **Description**: Purpose of the workspace
   - **Visibility**: Private or team workspace

### Workspace Members

**Adding Members:**
1. Go to workspace settings
2. Click "Invite Members"
3. Enter email addresses
4. Assign roles (Owner, Admin, Member)

**Role Permissions:**
- **Owner**: Full control, can delete workspace
- **Admin**: Manage members, agents, datasets
- **Member**: Can create and use agents

### Workspace Settings

- **General**: Basic information and visibility
- **Members**: Team management
- **Integrations**: External service connections
- **Usage**: Monitoring and limits

## Working with Datasets

### Creating Datasets

1. Navigate to "Datasets" in your workspace
2. Click "Create Dataset"
3. Configure dataset:
   - **Name**: Descriptive identifier
   - **Description**: Content and purpose
   - **Vector Store**: Choose storage backend
   - **Embedding Model**: Text processing model

### Uploading Documents

**Supported File Types:**
- PDF files (.pdf)
- Text files (.txt, .md)
- Word documents (.docx)
- CSV files (.csv)
- JSON files (.json)

**Upload Process:**
1. Click "Upload Documents" in your dataset
2. Select files from your computer
3. Wait for processing status
4. Review chunking and embedding results

### Document Processing

**Automatic Processing:**
- Text extraction from documents
- Intelligent chunking (1000 characters with 200 overlap)
- Vector embedding for semantic search
- Metadata extraction

**Processing Status:**
- **Uploaded**: File received, waiting for processing
- **Processing**: Text extraction and chunking
- **Indexed**: Embeddings created and searchable
- **Error**: Processing failed (check error details)

### Using Datasets in Agents

1. Add a Retrieval node to your agent
2. Select your dataset in node configuration
3. Set similarity parameters
4. Test retrieval with sample queries

## Running Agents

### Manual Execution

1. Open your agent from the agent list
2. Click "Run Agent"
3. Provide input data
4. Monitor execution in real-time
5. Review results and logs

### Batch Processing

1. Go to "Batch Runs" in your agent
2. Upload CSV or JSON file with multiple inputs
3. Start batch processing
4. Download results when complete

### Real-time Monitoring

**Execution Dashboard:**
- Live status updates
- Node-by-node progress
- Intermediate results
- Error messages and warnings
- Performance metrics

**Event Stream:**
- Detailed execution logs
- Token usage tracking
- Timing information
- Error diagnostics

### Understanding Results

**Output Formats:**
- **JSON**: Structured data for applications
- **Text**: Human-readable responses
- **Files**: Generated documents or reports

**Metrics:**
- Execution time
- Token usage
- Cost estimation
- Success rate

## Collaboration Features

### Sharing Agents

1. Open agent settings
2. Click "Share Agent"
3. Set sharing permissions:
   - **Private**: Only you
   - **Team**: Workspace members
   - **Public**: Anyone with link
4. Copy share link

### Version Management

**Agent Versions:**
- Automatic version creation on updates
- Version comparison
- Rollback capabilities
- Change tracking

**Collaborative Editing:**
- Real-time collaboration on agent design
- Conflict resolution
- Comment and discussion threads

### Team Workflows

**Approval Processes:**
- Agent review and approval
- Automated testing on changes
- Deployment pipelines

**Knowledge Base:**
- Shared templates and examples
- Best practices documentation
- Team guidelines

## Advanced Features

### Custom Tools

Create custom tools for specialized tasks:
- HTTP API integrations
- Database connections
- Custom Python functions
- External service integrations

### API Integration

Connect PromptFlow to external systems:
- REST API endpoints
- WebHooks for notifications
- Authentication methods
- Rate limiting and monitoring

### Performance Optimization

**Optimization Tips:**
- Use appropriate chunk sizes for datasets
- Optimize LLM parameters (temperature, tokens)
- Implement caching strategies
- Monitor resource usage

## Troubleshooting

### Common Issues

**Agent Not Running:**
- Check node connections
- Verify configuration
- Review error messages
- Test individual nodes

**Poor Results:**
- Adjust LLM parameters
- Improve prompt quality
- Add more context from datasets
- Refine workflow logic

**Performance Issues:**
- Reduce dataset size
- Optimize retrieval parameters
- Monitor token usage
- Consider caching strategies

**Integration Problems:**
- Verify API credentials
- Check endpoint URLs
- Test with simple requests
- Review rate limits

### Getting Help

**Support Resources:**
- 📚 [API Documentation](./api.md)
- 🔧 [Developer Guide](./developer-guide.md)
- 💬 Community forums
- 📧 Support email: support@promptflow.dev

**Community:**
- Discord server
- GitHub discussions
- Stack Overflow tag
- Blog and tutorials

## Best Practices

### Agent Design

1. **Start Simple**: Begin with basic workflows
2. **Iterate Often**: Test and improve gradually
3. **Document Clearly**: Use meaningful node names and descriptions
4. **Handle Errors**: Include error handling in workflows
5. **Monitor Performance**: Track usage and optimize

### Data Management

1. **Clean Data**: Ensure data quality before upload
2. **Organize Datasets**: Use clear naming conventions
3. **Regular Updates**: Keep datasets current
4. **Access Control**: Manage data permissions properly

### Security

1. **Strong Authentication**: Use unique passwords
2. **API Keys**: Rotate keys regularly
3. **Data Privacy**: Be mindful of sensitive information
4. **Permissions**: Grant minimal necessary access

## Next Steps

- 🚀 [Explore API endpoints](./api.md)
- 🔧 [Set up development environment](./developer-guide.md)
- 📖 [View examples and templates](./examples/)
- 💬 [Join our community](https://discord.gg/promptflow)

For additional help, contact our support team or community forums.