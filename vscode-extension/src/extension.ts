import * as vscode from 'vscode';
import { ClientSession, StdioServerParameters } from '@modelcontextprotocol/sdk/client/index.js';
import { stdio_client } from '@modelcontextprotocol/sdk/client/stdio.js';

export function activate(context: vscode.ExtensionContext) {
    console.log('Fabric MCP Client extension is now active!');

    // Register command to list eventstreams
    let listEventstreamsCommand = vscode.commands.registerCommand('fabric-mcp.listEventstreams', async () => {
        try {
            const workspaceId = await vscode.window.showInputBox({
                prompt: 'Enter workspace ID',
                placeHolder: 'e.g., 12345678-1234-1234-1234-123456789012'
            });

            const authToken = await vscode.window.showInputBox({
                prompt: 'Enter authorization token',
                placeHolder: 'Bearer token',
                password: true
            });

            if (!workspaceId || !authToken) {
                vscode.window.showErrorMessage('Workspace ID and auth token are required');
                return;
            }

            const result = await callMcpTool('eventstream_list', {
                workspace_id: workspaceId,
                authorization_token: authToken
            });

            // Show results in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: JSON.stringify(result, null, 2),
                language: 'json'
            });
            await vscode.window.showTextDocument(doc);

        } catch (error) {
            vscode.window.showErrorMessage(`Error listing eventstreams: ${error}`);
        }
    });

    // Register command to query Kusto
    let queryKustoCommand = vscode.commands.registerCommand('fabric-mcp.queryKusto', async () => {
        try {
            const clusterUri = await vscode.window.showInputBox({
                prompt: 'Enter Kusto cluster URI',
                placeHolder: 'e.g., https://mycluster.kusto.windows.net'
            });

            const query = await vscode.window.showInputBox({
                prompt: 'Enter KQL query',
                placeHolder: 'e.g., MyTable | take 10'
            });

            if (!clusterUri || !query) {
                vscode.window.showErrorMessage('Cluster URI and query are required');
                return;
            }

            const result = await callMcpTool('kusto_query', {
                cluster_uri: clusterUri,
                query: query
            });

            // Show results in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: JSON.stringify(result, null, 2),
                language: 'json'
            });
            await vscode.window.showTextDocument(doc);

        } catch (error) {
            vscode.window.showErrorMessage(`Error querying Kusto: ${error}`);
        }
    });

    context.subscriptions.push(listEventstreamsCommand);
    context.subscriptions.push(queryKustoCommand);
}

async function callMcpTool(toolName: string, args: any): Promise<any> {
    const serverParams: StdioServerParameters = {
        command: 'uvx',
        args: ['microsoft-fabric-rti-mcp']
    };

    return new Promise((resolve, reject) => {
        stdio_client(serverParams).then(async ([read, write]) => {
            const session = new ClientSession(read, write);
            
            try {
                await session.initialize();
                const result = await session.call_tool(toolName, args);
                resolve(result.content);
            } catch (error) {
                reject(error);
            } finally {
                // Clean up connection
                write.end();
            }
        }).catch(reject);
    });
}

export function deactivate() {}
