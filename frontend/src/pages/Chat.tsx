import {
  useState,
  type FormEvent,
} from "react";

import {
  Bot,
  Send,
  User,
  FileText,
  Loader2,
} from "lucide-react";

import api from "../services/api";


interface Source {
  document_name: string;
  version: string;
  page_number: number | null;
}


interface AskResponse {
  answer: string;
  confidence: string;
  sources: Source[];
}


interface Message {
  role: "user" | "assistant";
  content: string;
  confidence?: string;
  sources?: Source[];
}


export default function Chat() {

  const [messages, setMessages] = useState<Message[]>([]);

  const [question, setQuestion] = useState("");

  const [loading, setLoading] = useState(false);


  const askQuestion = async (
    event: FormEvent
  ) => {

    event.preventDefault();


    const query = question.trim();


    if (!query || loading) {
      return;
    }


    // -------------------------------------------------
    // Add user message
    // -------------------------------------------------

    setMessages((previous) => [

      ...previous,

      {
        role: "user",
        content: query,
      },

    ]);


    setQuestion("");

    setLoading(true);


    try {

      // -------------------------------------------------
      // Ask backend
      // -------------------------------------------------

      const response = await api.post<AskResponse>(
        "/ask",
        {
          query,
        }
      );


      // -------------------------------------------------
      // Add AI response
      // -------------------------------------------------

      setMessages((previous) => [

        ...previous,

        {
          role: "assistant",
          content: response.data.answer,
          confidence:
            response.data.confidence,
          sources:
            response.data.sources,
        },

      ]);

    } catch (error) {

      console.error(
        "AI question failed:",
        error
      );


      setMessages((previous) => [

        ...previous,

        {
          role: "assistant",
          content:
            "I couldn't connect to the knowledge service. Please try again.",
        },

      ]);

    } finally {

      setLoading(false);

    }

  };


  return (

    <div className="chat-page">

      {/* =================================================
          HEADER
      ================================================= */}

      <div className="page-heading">

        <div>

          <h1>
            AI Knowledge Assistant
          </h1>

          <p>
            Ask questions about your
            enterprise knowledge base.
          </p>

        </div>

      </div>


      {/* =================================================
          CHAT AREA
      ================================================= */}

      <div className="chat-container">


        {/* Empty state */}

        {messages.length === 0 && (

          <div className="chat-empty">

            <div className="chat-empty-icon">

              <Bot size={32} />

            </div>


            <h2>
              How can I help you?
            </h2>


            <p>
              Ask me about company policies,
              documents, procedures and
              enterprise knowledge.
            </p>


            <div className="suggested-questions">

              <button
                type="button"
                onClick={() =>
                  setQuestion(
                    "What is the leave policy?"
                  )
                }
              >
                What is the leave policy?
              </button>


              <button
                type="button"
                onClick={() =>
                  setQuestion(
                    "How many days of casual leave are employees entitled to?"
                  )
                }
              >
                How many days of casual leave?
              </button>


              <button
                type="button"
                onClick={() =>
                  setQuestion(
                    "Who approves employee leave?"
                  )
                }
              >
                Who approves employee leave?
              </button>

            </div>

          </div>

        )}


        {/* =================================================
            MESSAGES
        ================================================= */}

        {messages.map(
          (message, index) => (

            <div
              className={
                message.role === "user"
                  ? "chat-message user-message"
                  : "chat-message assistant-message"
              }
              key={index}
            >


              {/* Avatar */}

              <div className="chat-avatar">

                {message.role === "user" ? (

                  <User size={18} />

                ) : (

                  <Bot size={18} />

                )}

              </div>


              {/* Message */}

              <div className="chat-bubble">

                <div className="chat-message-text">

                  {message.content}

                </div>


                {/* Confidence */}

                {message.confidence && (

                  <div className="chat-confidence">

                    <span>
                      Confidence
                    </span>

                    <strong>
                      {message.confidence
                        .charAt(0)
                        .toUpperCase()
                        +
                        message.confidence.slice(1)}
                    </strong>

                  </div>

                )}


                {/* Sources */}

                {message.sources &&
                  message.sources.length > 0 && (

                  <div className="chat-sources">

                    <div className="chat-sources-title">

                      <FileText size={15} />

                      <span>
                        Sources
                      </span>

                    </div>


                    {message.sources.map(
                      (source, sourceIndex) => (

                        <div
                          className="chat-source"
                          key={sourceIndex}
                        >

                          <div>

                            <strong>
                              {
                                source.document_name
                              }
                            </strong>

                          </div>


                          <span>

                            Version{" "}
                            {source.version}

                            {source.page_number !==
                              null && (
                              <>
                                {" "}• Page{" "}
                                {
                                  source.page_number
                                }
                              </>
                            )}

                          </span>

                        </div>

                      )
                    )}

                  </div>

                )}

              </div>

            </div>

          )
        )}


        {/* =================================================
            LOADING
        ================================================= */}

        {loading && (

          <div className="chat-message assistant-message">

            <div className="chat-avatar">

              <Bot size={18} />

            </div>


            <div className="chat-bubble">

              <div className="chat-loading">

                <Loader2
                  size={18}
                  className="spin"
                />

                <span>
                  Searching enterprise knowledge...
                </span>

              </div>

            </div>

          </div>

        )}

      </div>


      {/* =================================================
          INPUT
      ================================================= */}

      <form
        className="chat-input-area"
        onSubmit={askQuestion}
      >

        <input
          type="text"
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          placeholder="Ask a question about enterprise knowledge..."
          disabled={loading}
        />


        <button
          type="submit"
          disabled={
            loading ||
            !question.trim()
          }
        >

          {loading ? (

            <Loader2
              size={20}
              className="spin"
            />

          ) : (

            <Send size={20} />

          )}

        </button>

      </form>

    </div>

  );
}