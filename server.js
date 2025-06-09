// cow714 OSRS Community Controller Backend Server
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"],
        credentials: true
    }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Configuration
const PORT = process.env.PORT || 3000;
const RATE_LIMIT = 1000; // 1 second between commands per user
const MAX_QUEUE_SIZE = 10;

// State management
const connectedUsers = new Map();
const pcClients = new Set();
const commandQueue = [];
let userCommandTimes = new Map();

// Rate limiting function
function isRateLimited(userId) {
    const now = Date.now();
    const lastCommand = userCommandTimes.get(userId) || 0;
    
    if (now - lastCommand < RATE_LIMIT) {
        return true;
    }
    
    userCommandTimes.set(userId, now);
    return false;
}

// Execute command on PC (send to connected PC clients)
function executeCommand(command) {
    try {
        console.log('Sending command to PC clients:', command);
        
        if (pcClients.size === 0) {
            console.warn('⚠️  No PC clients connected!');
            return;
        }
        
        // Send command to all connected PC clients
        pcClients.forEach(pcId => {
            io.to(pcId).emit('execute_command', command);
        });
        
    } catch (error) {
        console.error('Failed to send command to PC:', error);
    }
}

// Process command queue
function processCommandQueue() {
    if (commandQueue.length > 0) {
        const command = commandQueue.shift();
        executeCommand(command);
        
        // Broadcast command execution to all clients
        io.emit('command_executed', {
            command: command,
            queueLength: commandQueue.length,
            timestamp: Date.now()
        });
    }
}

// Process queue every 500ms to prevent spam
setInterval(processCommandQueue, 500);

// Socket.io connection handling
io.on('connection', (socket) => {
    const userId = socket.id;
    connectedUsers.set(userId, {
        id: userId,
        connectedAt: Date.now(),
        commandCount: 0
    });
    
    console.log(`User connected: ${userId} (Total: ${connectedUsers.size})`);
    
    // Handle PC client registration
    socket.on('register_pc', () => {
        pcClients.add(socket.id);
        console.log(`🖥️  PC client registered: ${socket.id} (Total PC clients: ${pcClients.size})`);
        
        // Remove from regular users if it was there
        connectedUsers.delete(socket.id);
        
        socket.emit('pc_registered', { status: 'success' });
    });
    
    // Handle command completion from PC
    socket.on('command_completed', (data) => {
        console.log('✅ Command completed on PC:', data);
        io.emit('command_status', data);
    });
    
    // Send current stats to new user
    socket.emit('stats_update', {
        connectedUsers: connectedUsers.size,
        queueLength: commandQueue.length,
        pcClientsConnected: pcClients.size
    });
    
    // Broadcast user count update
    io.emit('user_count_update', connectedUsers.size);
    
    // Handle incoming commands
    socket.on('command', (data) => {
        try {
            // Rate limiting
            if (isRateLimited(userId)) {
                socket.emit('rate_limited', {
                    message: 'Please wait before sending another command',
                    cooldown: RATE_LIMIT
                });
                return;
            }
            
            // Validate command
            if (!data || !data.action) {
                socket.emit('error', { message: 'Invalid command format' });
                return;
            }
            
            // Check queue size
            if (commandQueue.length >= MAX_QUEUE_SIZE) {
                socket.emit('queue_full', {
                    message: 'Command queue is full, please try again later'
                });
                return;
            }
            
            // Add command to queue
            const command = {
                userId: userId,
                action: data.action,
                data: data.data || {},
                timestamp: Date.now()
            };
            
            commandQueue.push(command);
            
            // Update user stats
            const user = connectedUsers.get(userId);
            if (user) {
                user.commandCount++;
            }
            
            console.log(`Command queued from ${userId}:`, command);
            
            // Acknowledge command received
            socket.emit('command_queued', {
                position: commandQueue.length,
                command: command
            });
            
            // Broadcast queue update to all clients
            io.emit('queue_update', {
                queueLength: commandQueue.length,
                lastCommand: {
                    action: data.action,
                    user: userId.substring(0, 8) + '...'
                }
            });
            
        } catch (error) {
            console.error('Error processing command:', error);
            socket.emit('error', { message: 'Failed to process command' });
        }
    });
    
    // Handle disconnection
    socket.on('disconnect', () => {
        // Check if it was a PC client
        if (pcClients.has(socket.id)) {
            pcClients.delete(socket.id);
            console.log(`🖥️  PC client disconnected: ${socket.id} (Total PC clients: ${pcClients.size})`);
        } else {
            // Regular user disconnect
            connectedUsers.delete(userId);
            userCommandTimes.delete(userId);
            console.log(`User disconnected: ${userId} (Total: ${connectedUsers.size})`);
            
            // Broadcast user count update
            io.emit('user_count_update', connectedUsers.size);
        }
    });
    
    // Handle ping for connection health
    socket.on('ping', () => {
        socket.emit('pong', { timestamp: Date.now() });
    });
});

// REST API endpoints
app.get('/api/stats', (req, res) => {
    res.json({
        connectedUsers: connectedUsers.size,
        queueLength: commandQueue.length,
        pcClientsConnected: pcClients.size,
        totalCommands: Array.from(connectedUsers.values())
            .reduce((sum, user) => sum + user.commandCount, 0)
    });
});

app.get('/api/queue', (req, res) => {
    res.json({
        queue: commandQueue.map(cmd => ({
            action: cmd.action,
            timestamp: cmd.timestamp,
            user: cmd.userId.substring(0, 8) + '...'
        }))
    });
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        timestamp: Date.now(),
        uptime: process.uptime(),
        pcClients: pcClients.size,
        users: connectedUsers.size
    });
});

// Start server
server.listen(PORT, () => {
    console.log('🎮 cow714 OSRS Community Controller Server Started!');
    console.log(`📡 Server running on port ${PORT}`);
    console.log(`🌐 WebSocket endpoint: ws://localhost:${PORT}`);
    console.log(`📊 Stats API: http://localhost:${PORT}/api/stats`);
    console.log('\n📝 Next steps:');
    console.log('1. Start pc_client.py on your gaming PC');
    console.log('2. Share your public URL with viewers');
    console.log('3. Let the community control cow714!');
    console.log('\n⚙️  Configuration:');
    console.log(`- Rate limit: ${RATE_LIMIT}ms between commands`);
    console.log(`- Max queue size: ${MAX_QUEUE_SIZE} commands`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down server...');
    server.close(() => {
        console.log('✅ Server shut down gracefully');
        process.exit(0);
    });
});
