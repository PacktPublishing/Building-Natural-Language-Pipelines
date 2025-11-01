def pretty_print_rag_answer(answer, rag_type="RAG", query=None):
    """
    Pretty print function to display RAG answers in a readable format.
    
    Args:
        answer: Dictionary containing 'replies' and optionally 'documents'
        rag_type: String indicating the type of RAG system (e.g., "Hybrid RAG", "Naive RAG")
        query: Optional query string to display
    """
    print("="*80)
    print(f"🔍 {rag_type.upper()} ANSWER")
    print("="*80)
    
    if query:
        print(f"📝 Query: {query}")
        print("-"*80)
    
    # Display the main reply/answer
    if 'replies' in answer and answer['replies']:
        print("💬 Answer:")
        for i, reply in enumerate(answer['replies'], 1):
            if len(answer['replies']) > 1:
                print(f"\n{i}. {reply}")
            else:
                # Wrap text for better readability
                import textwrap
                wrapped_text = textwrap.fill(reply, width=75, initial_indent="   ", subsequent_indent="   ")
                print(f"{wrapped_text}")
    
    # Display source documents if available
    if 'documents' in answer and answer['documents']:
        print(f"\n📚 Source Documents ({len(answer['documents'])} found):")
        print("-"*50)
        for i, doc in enumerate(answer['documents'][:5], 1):  # Show max 5 documents
            # Extract metadata if available
            source = getattr(doc, 'meta', {}).get('source', 'Unknown source')
            if hasattr(doc, 'content'):
                content_preview = doc.content[:150] + "..." if len(doc.content) > 150 else doc.content
                print(f"{i}. Source: {source}")
                print(f"   Preview: {content_preview}")
                print()
        
        if len(answer['documents']) > 5:
            print(f"   ... and {len(answer['documents']) - 5} more documents")
    
    print("="*80)
    print()

# Alternative compact version
def compact_print_rag_answer(answer, rag_type="RAG"):
    """
    Compact version of pretty print for quick comparison.
    """
    print(f"🔹 {rag_type}: ", end="")
    if 'replies' in answer and answer['replies']:
        # Show first 200 characters
        reply = answer['replies'][0]
        if len(reply) > 200:
            print(reply[:200] + "...")
        else:
            print(reply)
    
    if 'documents' in answer and answer['documents']:
        print(f"   📚 Based on {len(answer['documents'])} documents")
    print()