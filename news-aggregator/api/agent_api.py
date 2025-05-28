"""
Agent API - RESTful endpoints for individual agent calls
"""
from flask import Blueprint, request, jsonify
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.news_agent_coordinator import NewsAgentCoordinator
from agents.jargon_agent import JargonAgent
from agents.viewpoints_agent import ViewpointsAgent
from agents.fact_check_agent import FactCheckAgent
from agents.bias_agent import BiasAnalysisAgent
from agents.timeline_agent import TimelineAgent
from agents.expert_agent import ExpertOpinionsAgent
from config.config import XAI_API_KEY


# Create Blueprint
agent_api = Blueprint('agent_api', __name__, url_prefix='/api/agents')

# Initialize coordinator and individual agents
coordinator = NewsAgentCoordinator()
# Use the same agents from the coordinator to avoid duplication
individual_agents = coordinator.agents


@agent_api.route('/health', methods=['GET'])
def health_check():
    """Health check for agent API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'available_agents': list(individual_agents.keys()),
        'api_key_configured': bool(XAI_API_KEY)
    })


@agent_api.route('/list', methods=['GET'])
def list_agents():
    """List all available agents with their information"""
    agent_info = coordinator.get_agent_info()
    
    return jsonify({
        'status': 'success',
        'agents': agent_info,
        'total_agents': len(agent_info)
    })


@agent_api.route('/<agent_name>/analyze', methods=['POST'])
def analyze_with_agent(agent_name: str):
    """
    Analyze content with a specific agent
    
    Expected JSON payload:
    {
        "content": "Article content to analyze",
        "url": "Optional article URL",
        "config": {}  # Optional agent-specific config
    }
    """
    try:
        # Validate agent exists
        if agent_name not in individual_agents:
            return jsonify({
                'status': 'error',
                'error': f'Agent "{agent_name}" not found',
                'available_agents': list(individual_agents.keys())
            }), 404
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'JSON payload required'
            }), 400
        
        content = data.get('content')
        url = data.get('url', '')
        config = data.get('config', {})
        
        if not content:
            return jsonify({
                'status': 'error',
                'error': 'Content is required'
            }), 400
        
        print(f"[AgentAPI] {agent_name} analysis requested for content: {len(content)} chars")
        
        # Run analysis
        start_time = datetime.now()
        
        async def run_analysis():
            return await coordinator._run_agent_analysis(
                individual_agents[agent_name], 
                agent_name, 
                content, 
                url
            )
        
        # Execute async analysis
        result = asyncio.run(run_analysis())
        
        # Format response
        response = {
            'status': 'success',
            'agent': agent_name,
            'analysis_status': result.status,
            'duration_seconds': result.duration,
            'data': result.data if result.status == 'success' else None,
            'error': result.error_message if result.status != 'success' else None,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[AgentAPI] {agent_name} analysis completed: {result.status}")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[AgentAPI] Error in {agent_name} analysis: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'agent': agent_name
        }), 500


@agent_api.route('/analyze-multiple', methods=['POST'])
def analyze_multiple():
    """
    Analyze content with multiple agents
    
    Expected JSON payload:
    {
        "content": "Article content to analyze",
        "url": "Optional article URL",
        "agents": ["jargon", "bias", "viewpoints"],  # Optional, defaults to all
        "parallel": true  # Optional, run in parallel (default) or sequential
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'JSON payload required'
            }), 400
        
        content = data.get('content')
        url = data.get('url', '')
        requested_agents = data.get('agents', list(individual_agents.keys()))
        parallel = data.get('parallel', True)
        
        if not content:
            return jsonify({
                'status': 'error',
                'error': 'Content is required'
            }), 400
        
        # Validate requested agents
        invalid_agents = [a for a in requested_agents if a not in individual_agents]
        if invalid_agents:
            return jsonify({
                'status': 'error',
                'error': f'Invalid agents: {invalid_agents}',
                'available_agents': list(individual_agents.keys())
            }), 400
        
        print(f"[AgentAPI] Multi-agent analysis requested: {requested_agents}")
        print(f"[AgentAPI] Content length: {len(content)} chars, Parallel: {parallel}")
        
        # Run analysis
        start_time = datetime.now()
        
        if parallel:
            # Run in parallel (faster)
            async def run_parallel_analysis():
                return await coordinator.analyze_article_subset(content, url, requested_agents)
            
            results = asyncio.run(run_parallel_analysis())
        else:
            # Run sequentially (for debugging or rate limiting)
            results = {}
            for agent_name in requested_agents:
                async def run_single_analysis():
                    return await coordinator._run_agent_analysis(
                        individual_agents[agent_name], 
                        agent_name, 
                        content, 
                        url
                    )
                
                result = asyncio.run(run_single_analysis())
                results[agent_name] = result
        
        # Format response
        total_duration = (datetime.now() - start_time).total_seconds()
        
        formatted_results = {}
        successful_analyses = []
        failed_analyses = []
        
        for agent_name, result in results.items():
            formatted_results[agent_name] = {
                'status': result.status,
                'duration_seconds': result.duration,
                'data': result.data if result.status == 'success' else None,
                'error': result.error_message if result.status != 'success' else None
            }
            
            if result.status == 'success':
                successful_analyses.append(agent_name)
            else:
                failed_analyses.append(agent_name)
        
        response = {
            'status': 'success',
            'requested_agents': requested_agents,
            'successful_analyses': successful_analyses,
            'failed_analyses': failed_analyses,
            'parallel_execution': parallel,
            'total_duration_seconds': total_duration,
            'results': formatted_results,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[AgentAPI] Multi-agent analysis completed: {len(successful_analyses)}/{len(requested_agents)} successful")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[AgentAPI] Error in multi-agent analysis: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@agent_api.route('/analyze-full', methods=['POST'])
def analyze_full():
    """
    Analyze content with all agents (convenience endpoint)
    
    Expected JSON payload:
    {
        "content": "Article content to analyze",
        "url": "Optional article URL"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'JSON payload required'
            }), 400
        
        content = data.get('content')
        url = data.get('url', '')
        
        if not content:
            return jsonify({
                'status': 'error',
                'error': 'Content is required'
            }), 400
        
        print(f"[AgentAPI] Full analysis requested for content: {len(content)} chars")
        
        # Run full analysis
        async def run_full_analysis():
            return await coordinator.analyze_article_full(content, url)
        
        results = asyncio.run(run_full_analysis())
        
        # Format using coordinator's built-in formatter
        formatted_response = coordinator.format_results_for_storage(results)
        
        response = {
            'status': 'success',
            'type': 'full_analysis',
            'analyses': formatted_response['analyses'],
            'metadata': formatted_response['metadata'],
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[AgentAPI] Full analysis completed: {formatted_response['metadata']['successful_agents']}/{formatted_response['metadata']['total_agents']} successful")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[AgentAPI] Error in full analysis: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@agent_api.route('/<agent_name>/config', methods=['GET'])
def get_agent_config(agent_name: str):
    """Get configuration for a specific agent"""
    if agent_name not in individual_agents:
        return jsonify({
            'status': 'error',
            'error': f'Agent "{agent_name}" not found'
        }), 404
    
    agent_info = coordinator.get_agent_info().get(agent_name, {})
    
    return jsonify({
        'status': 'success',
        'agent': agent_name,
        'config': agent_info
    })


@agent_api.route('/batch', methods=['POST'])  
def batch_analyze():
    """
    Analyze multiple content pieces with specified agents
    
    Expected JSON payload:
    {
        "tasks": [
            {
                "id": "task1",
                "content": "Content 1",
                "url": "URL 1",
                "agents": ["jargon", "bias"]
            },
            {
                "id": "task2", 
                "content": "Content 2",
                "url": "URL 2",
                "agents": ["viewpoints"]
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data or 'tasks' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Tasks array required'
            }), 400
        
        tasks = data['tasks']
        
        print(f"[AgentAPI] Batch analysis requested: {len(tasks)} tasks")
        
        # Process each task
        results = []
        start_time = datetime.now()
        
        for task in tasks:
            task_id = task.get('id', f'task_{len(results)}')
            content = task.get('content')
            url = task.get('url', '')
            agents = task.get('agents', ['jargon'])  # Default to jargon only
            
            if not content:
                results.append({
                    'task_id': task_id,
                    'status': 'error',
                    'error': 'Content required for task'
                })
                continue
            
            try:
                # Run analysis for this task
                async def run_task_analysis():
                    return await coordinator.analyze_article_subset(content, url, agents)
                
                task_results = asyncio.run(run_task_analysis())
                
                # Format task result
                task_response = {
                    'task_id': task_id,
                    'status': 'success',
                    'requested_agents': agents,
                    'results': {}
                }
                
                for agent_name, result in task_results.items():
                    task_response['results'][agent_name] = {
                        'status': result.status,
                        'data': result.data if result.status == 'success' else None,
                        'error': result.error_message if result.status != 'success' else None
                    }
                
                results.append(task_response)
                
            except Exception as e:
                results.append({
                    'task_id': task_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        response = {
            'status': 'success',
            'total_tasks': len(tasks),
            'completed_tasks': len(results),
            'total_duration_seconds': total_duration,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[AgentAPI] Batch analysis completed: {len(results)} tasks processed")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[AgentAPI] Error in batch analysis: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500