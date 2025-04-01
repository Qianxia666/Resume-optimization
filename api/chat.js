export default async (req, res) => {
  const { question } = await req.body;
  
  try {
    const apiKey = req.body.apiKey || process.env.OPENAI_API_KEY;
    const baseUrl = req.body.baseUrl || process.env.OPENAI_API_BASE;
    
    const response = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: req.body.model || process.env.DEFAULT_MODEL || "gpt-3.5-turbo",
        messages: (() => {
          const systemMessage = `假如你是一名资深简历提升官，请使用STAR+改写简历，并且最后提供完整输出，帮助更多应届大学生顺利找到他们的工作 输出限制：1.请不要使用任何表情符号 2.请在一个自然段内完整输出 3.请不要过度夸大，请符合岗位实际 4.语言请说人话，平白直叙，拒绝任何行业黑话`;
          const messages = [];
          if (systemMessage) {
            messages.push({ 
              role: "system", 
              content: systemMessage 
            });
          }
          messages.push({ 
            role: "user", 
            content: question 
          });
          return messages;
        })()
      })
    });

    const data = await response.json();
    res.status(200).json({ 
      answer: data.choices[0].message.content 
    });
  } catch (error) {
    res.status(500).json({ 
      answer: `API请求失败: ${error.message}` 
    });
  }
};
